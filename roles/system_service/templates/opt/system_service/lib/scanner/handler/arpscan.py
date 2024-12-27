import threading
import socket
import traceback

from datetime import datetime, timedelta
import time
import re
import math
import logging

from smartserver import command

from lib.scanner.handler import _handler

from lib.scanner.dto._changeable import Changeable
from lib.scanner.dto.device import Device, Connection
from lib.scanner.dto.device_stat import DeviceStat
from lib.scanner.dto.event import Event

from lib.scanner.helper import Helper

class AddressHelper():
    def knock(address_family,ip_address):
        s = socket.socket(address_family, socket.SOCK_DGRAM)
        s.setblocking(False)
        socket_address = (ip_address, 5353)
        s.sendto(b'', socket_address)
        s.close()
        
    def getAddressFamily(ip_address):
        address_family, _, _, _, (ip_address, _) = socket.getaddrinfo(
            host=ip_address,
            port=None,
            flags=socket.AI_ADDRCONFIG
        )[0]
        return address_family

class DeviceChecker(threading.Thread):
    '''Device client'''
    def __init__(self, arpscanner, cache, device, stat, interface, type, timeout):
        threading.Thread.__init__(self) 
        
        self.is_running = True
        self.event = threading.Event()

        self.arpscanner = arpscanner
        self.cache = cache
        self.device = device
        self.stat = stat
        self.interface = interface

        self.type = type

        self.timeout = timeout

        self.longCheck = False

    def _isRunning(self):
        return self.is_running
      
    def run(self):
        logging.info("Device checker for {} started".format(self.device))
        is_supended = False
        
        while self._isRunning():
            try:
                if is_supended:
                    logging.warning("Resume DeviceChecker")
                    is_supended = False
                
                self.event.wait(60 if self.stat.isOnline() else 300)
                self.event.clear()
                    
                if not self._isRunning():
                    break

                if self.stat.isOnline():
                    self.longCheck = True

                arp_timeout = 10
                ping_timeout = 10

                if self.longCheck:
                    total_timeout = self.timeout
                else:
                    # non android devices neededs more retries because of for multiple calls of 'knock' during offline check time
                    total_timeout = ( 1 if self.type == "android" else 3 ) * arp_timeout
                    
                startTime = datetime.now()
                
                ip_address = self.device.getIP()
                mac_address = self.device.getMAC()
                address_family = AddressHelper.getAddressFamily(ip_address)
                
                loopIndex = 0
                while self._isRunning():
                    if self.type != "android":
                        AddressHelper.knock(self.address_family,ip_address)
                        time.sleep(0.05)

                    methods = ["arping"]
                    answering_mac = Helper.getMacFromArpPing(ip_address, self.interface, arp_timeout, self._isRunning)
                    if answering_mac is None and self.longCheck:
                        methods.append("ping")
                        answering_mac = Helper.getMacFromPing(ip_address, ping_timeout, self._isRunning)
                        
                    duration = round((datetime.now() - startTime).total_seconds(),2)

                    if answering_mac is not None:
                        if answering_mac != mac_address:
                            logging.info("Device {} has wrong ip. Answering MAC was {}".format(self.device,answering_mac))
                            self.arpscanner._handleDeviceIPChange(self.device, self.stat)

                            self.is_running = False
                            self.arpscanner._stopDeviceChecker(mac_address)
                        else:
                            logging.info("Device {} is online. Checked with {} in {} seconds".format(ip_address, " & ".join(methods),duration))
                            self.lastSeen = datetime.now()
                            self.stat.setLastSeen(True) # no lock needed
                            self.arpscanner._setDeviceOnline(self.stat, True)
                        break
                        
                    if duration >= total_timeout:
                        logging.info("Device {} is offline. Checked with {} in {} seconds".format(ip_address," & ".join(methods),duration))
                        self.arpscanner._setDeviceOnline(self.stat, False)
                        break

                self.longCheck = self.stat.isOnline()
                    
            except Exception as e:
                self.cache.cleanLocks(self)
                logging.error("DeviceChecker got unexpected exception. Will suspend for 15 minutes.")
                logging.error(traceback.format_exc())
                is_supended = True
                    
            if is_supended:
                self.event.wait(900)
                self.event.clear()

        logging.info("Device checker for {} stopped".format(self.device))

    def wakeup(self):
        self.event.set()

    def terminate(self):
        self.is_running = False
        self.event.set()
        self.join()
        
class DHCPListener(threading.Thread):
    def __init__(self, arpscanner, cache, interface):
        threading.Thread.__init__(self) 
        
        self.is_running = True
        self.event = threading.Event()

        self.arpscanner = arpscanner
        self.cache = cache
        
        self.interface = interface

        self.dhcpListenerProcess = None

    def run(self):
        logging.info("DHCP listener started")
        self.dhcpListenerProcess = Helper.dhcplisten(self.interface)
        if self.dhcpListenerProcess.returncode is not None:
            raise Exception("DHCP Listener not started")

        client_mac = None
        client_ip = None
        is_supended = False
        
        while self.is_running:
            if is_supended:
                logging.warning("Resume DHCPListener")
                is_supended = False

            output = self.dhcpListenerProcess.stdout.readline()
            #self.dhcpListenerProcess.stdout.flush()
            if output == '':
                if not self.is_running:
                    break
                if self.dhcpListenerProcess.poll() is not None:
                    raise Exception("DHCP Listener stopped")
            else:
                line = output.strip()
                if "BOOTP/DHCP" in line:
                    client_mac = None
                    client_ip = None
                else:
                    if line.startswith("Client-Ethernet-Address"):
                        match = re.search("^Client-Ethernet-Address ({})$".format("[a-z0-9]{2}:[a-z0-9]{2}:[a-z0-9]{2}:[a-z0-9]{2}:[a-z0-9]{2}:[a-z0-9]{2}"), line)
                        if match:
                            client_mac = match[1]
                        else:
                            logging.error("Can't parse Mac")
                            client_mac = None

                    elif line.startswith("Requested-IP") and client_mac is not None:
                        match = re.search("^Requested-IP.*?({})$".format("[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}"), line)
                        if match:
                            client_ip = match[1]
                        else:
                            logging.error("Can't parse IP")
                            client_ip = None
                            continue

                        try:
                            client_dns = self.cache.nslookup(client_ip)

                            self.cache.lock(self)
                            logging.info("New dhcp request for {} detected".format(client_ip))

                            device = self.cache.getDevice(client_mac)
                            device.setIP("dhcp_listener", 75, client_ip)
                            device.setDNS("nslookup", 1, client_dns)
                            self.cache.confirmDevice( self, device )

                            self.arpscanner._refreshDevice( device, True )

                            logging.info("New dhcp request for {} processed".format(client_ip))
                            self.cache.unlock(self)

                        except Exception as e:
                            self.cache.cleanLocks(self)
                            logging.error("DHCPListener checker got unexpected exception. Will suspend for 15 minutes.")
                            logging.error(traceback.format_exc())
                            is_supended = True

                        if is_supended:
                            self.event.wait(900)

                        client_mac = None
                        client_ip = None
                            
        rc = self.dhcpListenerProcess.poll()
        
        logging.info("DHCP listener stopped")

    def terminate(self):
        self.is_running = False
        if self.dhcpListenerProcess != None:
            self.dhcpListenerProcess.terminate()
        self.event.set()
        self.join()

class ArpScanner(_handler.Handler):
    def __init__(self, config, cache ):
        super().__init__(config,cache)
        
        self.lock = threading.Lock()
        self.registered_devices = {}

        self.dhcp_listener = DHCPListener(self, self.cache, self.config.main_interface)

    def start(self):
        self.dhcp_listener.start()
        
        super().start()

    def terminate(self):
        self.dhcp_listener.terminate()
        with self.lock:
            for mac in self.registered_devices:
                if self.registered_devices[mac] is not None:
                    self.registered_devices[mac].terminate()
        super().terminate()

    def _run(self):
        server_mac = "00:00:00:00:00:00"
        try:
            with open("/sys/class/net/{}/address".format(self.config.main_interface), 'r') as f:
                server_mac = f.read().strip()
        except (IOError, OSError) as e:
            pass

        ipv4_networks = []
        for network in self.config.internal_networks:
            match = re.match(r"[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}/.*", network)
            if match:
               ipv4_networks.append(network)

        while self._isRunning():
            if not self._isSuspended():
                try:
                    collected_arps = self._fetchArpResult(ipv4_networks)
                except Exception as e:
                    if not self.is_running:
                        break
                    raise e

                try:
                    processed_ips = {}
                    processed_macs = {}
                    for [ip, mac, dns, info] in collected_arps:
                        if mac not in processed_macs:
                            if ip not in processed_ips:
                                info = re.sub(r"\s\(DUP: [0-9]+\)", "", info) # eleminate dublicate marker
                                if info == "(Unknown)":
                                    info = None
                                processed_macs[mac] = {"mac": mac, "ip": ip, "dns": dns, "info": info}
                                processed_ips[ip] = mac
                    
                    self.cache.lock(self)
                    
                    with self.lock:
                        refreshed_macs = []
                        for entry in processed_macs.values():
                            mac = entry["mac"]
                            device = self.cache.getDevice(mac)
                            device.setIP("arpscan", 1, entry["ip"])
                            device.setDNS("nslookup", 1, entry["dns"])
                            device.setInfo(entry["info"])
                            self.cache.confirmDevice( self, device )

                            self._refreshDevice( device, True)
                            refreshed_macs.append(mac)

                        device = self.cache.getDevice(server_mac)
                        device.setIP("arpscan", 1, self.config.server_ip)
                        device.setDNS("nslookup", 1, self.config.server_domain)
                        device.setInfo(self.config.server_name)
                        self.cache.confirmDevice( self, device )

                        self._refreshDevice( device, True)
                        refreshed_macs.append(server_mac)

                        self.cache.unlock(self)

                        for device in self.cache.getDevices():
                            if device.getMAC() in refreshed_macs:
                                continue
                            self._cleanDevice(device)
                
                except Exception as e:
                    self.cache.cleanLocks(self)
                    self._handleUnexpectedException(e)

            suspend_timeout = self._getSuspendTimeout()
            if suspend_timeout > 0:
                timeout = suspend_timeout
            else:
                timeout = self.config.arp_scan_interval
                        
            self._wait(timeout)

    def _fetchArpResult(self, ipv4_networks):
        collected_arps = []
        for network in ipv4_networks:
            arp_result = Helper.arpscan(self.config.main_interface, network, self._isRunning)
            for arp_data in arp_result:
                ip = arp_data["ip"]
                mac = arp_data["mac"]
                info = arp_data["info"]
                
                dns = self.cache.nslookup(ip)
                        
                collected_arps.append([ip, mac, dns, info])
        return collected_arps
                
    def _cleanDevice(self, device):
        mac = device.getMAC()
        
        # UserIP's should be delegated to DeviceChecker
        if mac in self.registered_devices and self.registered_devices[mac] is not None:
            return

        stat = self.cache.getUnlockedDeviceStat(mac)
        if stat is None:
            logging.info("Can't check device {}. Stat is missing.".format(device))
            return

        now = datetime.now()

        last_seen = ( now - stat.getUnvalidatedLastSeen() ).total_seconds()
        if last_seen > self.config.arp_clean_timeout:
            self.cache.lock(self)
            self.cache.removeDevice(self, mac)
            self.cache.removeDeviceStat(self, mac)
            if self.registered_devices[mac] is not None:
                self.registered_devices[mac].terminate()
                del self.registered_devices[mac]
            self.cache.unlock(self)
            return

        if stat.isOnline() and last_seen > self.config.arp_offline_timeout:
            self._checkDevice(device, "Cleaned", True)

    def _checkDevice(self, device, type, mark_as_offline):
        if device.getMAC() not in self.registered_devices:
            self.cache.lock(self)
            self._refreshDevice( device, False)
            self.cache.unlock(self)

        if device.getMAC() in self.config.silent_device_macs or device.getIP() is None:
            logging.info("{} device {} skipped. No active checks applied".format(type, device))
        else:
            check_thread = threading.Thread(target=self._pingDevice, args=(device, type, mark_as_offline))
            check_thread.start()
    
    def _pingDevice(self, device, type, mark_as_offline):
        startTime = datetime.now()
        try:
            methods = ["arping"]
            answering_mac = Helper.getMacFromArpPing(device.getIP(), self.config.main_interface, 20 if mark_as_offline else 10, self._isRunning)
            if answering_mac is None and self.longCheck:
                methods.append("ping")
                answering_mac = Helper.getMacFromPing(device.getIP(), 20 if mark_as_offline else 10, self._isRunning)
            duration = round((datetime.now() - startTime).total_seconds(),2)
            if answering_mac is not None:
                if answering_mac != device.getMAC():
                    logging.info("{} device {} has wrong ip. Answering MAC was {}".format(type, device, answering_mac))
                    self._handleDeviceIPChange(device, self.cache.getUnlockedDeviceStat(device.getMAC()))
                else:
                    logging.info("{} device {} is online. Checked with {} in {} seconds".format(type, device, " & ".join(methods), duration))
                    self.cache.lock(self)
                    with self.lock:
                        self._refreshDevice(device, True)
                    self.cache.unlock(self)
            else:
                if mark_as_offline:
                    logging.info("{} device {} is offline. Checked with {} in {} seconds".format(type, device, " & ".join(methods), duration))
                    self._setDeviceOnline(stat, False)
                else:
                    logging.info("{} device {} not answering. Checked with {} in {} seconds".format(type, device, " & ".join(methods), duration))

        except Exception as e:
            self.cache.cleanLocks(self)
            self._handleUnexpectedException(e, None, -1)

    def _refreshDevice(self, device, validated):
        mac = device.getMAC()
        
        stat = self.cache.getDeviceStat(mac)
        stat.setLastSeen(validated)
        if validated:
            # no additional lock needed, because we already got a locked DeviceStat
            stat.setOnline(True)
        self.cache.confirmStat( self, stat )
        
        if mac not in self.registered_devices:
            self.registered_devices[mac] = None

        if self.registered_devices[mac] is not None:
            return
        
        if device.getIP() in self.config.user_devices:
            user_config = self.config.user_devices[device.getIP()]
            self.registered_devices[mac] = DeviceChecker(self, self.cache, device, stat, self.config.main_interface, user_config["type"], user_config["timeout"])
            self.registered_devices[mac].start()

    def _stopDeviceChecker(self, device):
        with self.lock:
            self.registered_devices[mac] = None

    def _setDeviceOnline(self,stat,flag):
        if stat.isOnline() == flag:
            return

        self.cache.lock(self)

        stat.lock(self)
        stat.setOnline(False)
        self.cache.confirmStat( self, stat )

        self.cache.unlock(self)

    def _handleDeviceIPChange(self, device, stat):
        self.cache.lock(self)

        device.lock(self)
        device.clearIP()
        device.unlock(self)

        if stat is not None:
            stat.lock(self)
            stat.setOnline(False)
            self.cache.confirmStat( self, stat )

        self.cache.unlock(self)

    def getEventTypes(self):
        return [ 
            { "types": [Event.TYPE_DEVICE], "actions": [Event.ACTION_CREATE,Event.ACTION_MODIFY], "details": None }
        ]

    def processEvents(self, events):
        disabled_devices = []
        unregistered_devices = []

        with self.lock:
            for event in events:
                device = event.getObject()

                connection = device.getConnection()
                if event.hasDetail("connection") and (connection is None or not connection.isEnabled()):
                    disabled_devices.append(device)
                elif device.getMAC() not in self.registered_devices:
                    unregistered_devices.append(device)

            if len(disabled_devices) > 0:
                for device in set(disabled_devices):
                    self._checkDevice(device, "Disabled", False)

            if len(unregistered_devices) > 0:
                for device in set(unregistered_devices):
                    self._checkDevice(device, "New", False)
            
