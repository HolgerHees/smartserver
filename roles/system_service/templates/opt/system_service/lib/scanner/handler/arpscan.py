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

        if self.type == "android":
            self.offlineArpRetries =  1
        else:
            # needed for multiple calls of 'knock' during offline check time
            self.offlineArpRetries =  int( math.floor( (timeout / 4) * 1 / 10 ) )
          
        # needed for multiple calls of 'ping' and 'knock' during online check time
        self.onlineArpRetries =  int( math.floor( (timeout / 4) * 3 / 10 ) )

        self.onlineArpCheckTime = int( math.floor( (timeout / 4) * 3 / self.onlineArpRetries ) )
        self.offlineArpCheckTime = int( math.floor( (timeout / 4) * 1 / self.offlineArpRetries ) )
        self.onlineSleepTime = timeout - (self.onlineArpRetries * self.onlineArpCheckTime)
        self.offlineSleepTime = timeout - (self.offlineArpRetries * self.offlineArpCheckTime)

        #self.lastSeen = datetime(1, 1, 1, 0, 0)
        #self.lastPublished = datetime(1, 1, 1, 0, 0)
        
        #self.isOnline = None

    def _isRunning(self):
        return self.is_running
      
    def run(self):
        logging.info("Device checker for {} started".format(self.device))
        is_supended = False
        
        while self._isRunning():
            events = []

            try:
                if is_supended:
                    logging.warning("Resume DeviceChecker")
                    is_supended = False
                
                sleepTime = self.onlineSleepTime if self.stat.isOnline() else self.offlineSleepTime
                
                self.event.wait(sleepTime)
                    
                if not self._isRunning():
                    break
                
                timeout = self.onlineArpCheckTime if self.stat.isOnline() else self.offlineArpCheckTime
                arpRetries = self.onlineArpRetries if self.stat.isOnline() else self.offlineArpRetries
                    
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
                    answering_mac = Helper.getMacFromArpPing(ip_address, self.interface, timeout, self._isRunning)
                    if answering_mac is None and self.stat.isOnline():
                        methods.append("ping")
                        answering_mac = Helper.getMacFromPing(ip_address, timeout, self._isRunning)
                        
                    duration = round((datetime.now() - startTime).total_seconds(),2)

                    if answering_mac is not None:
                        validated = answering_mac == mac_address
                        logging.info("Device {} is {} online. Checked with {} in {} seconds".format(ip_address, "validated" if validated else "unvalidated"," & ".join(methods),duration))
                        self.lastSeen = datetime.now()
                        self.stat.setLastSeen(validated) # no lock needed
                        if not self.stat.isOnline():
                            self.cache.lock(self)
                            self.stat.lock(self)
                            self.stat.setOnline(True)
                            self.cache.confirmStat( self, self.stat )
                            self.cache.unlock(self)
                        break
                        
                    loopIndex += 1
                    if loopIndex == arpRetries:
                        [_, maybe_offline, _] = self.arpscanner._possibleOfflineStates(self.stat)
                        if maybe_offline:
                            logging.info("Device {} is offline. Checked with {} in {} seconds".format(ip_address," & ".join(methods),duration))
                            if self.stat.isOnline():
                                self.cache.lock(self)
                                self.stat.lock(self)
                                self.stat.setOnline(False)
                                self.cache.confirmStat( self, self.stat )
                                self.cache.unlock(self)
                        break
                    
            except Exception as e:
                self.cache.cleanLocks(self, events)
                logging.error("DeviceChecker got unexpected exception. Will suspend for 15 minutes.")
                logging.error(traceback.format_exc())
                is_supended = True
                    
            if len(events) > 0:
                self.arpscanner._dispatch(events)
                
            if is_supended:
                self.event.wait(900)

        logging.info("Device checker for {} stopped".format(self.device))

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
        
        self.registered_devices = {}

        self.dhcp_listener = DHCPListener(self, self.cache, self.config.main_interface)

    def start(self):
        self.dhcp_listener.start()
        
        super().start()

    def terminate(self):
        self.dhcp_listener.terminate()
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
                        self._checkDevice(device)
                
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
                
    def _possibleOfflineStates(self, stat):
        now = datetime.now()
 
        validated_last_seen_diff = (now - stat.getValidatedLastSeen()).total_seconds()
        unvalidated_last_seen_diff = (now - stat.getUnvalidatedLastSeen()).total_seconds()
        
        # maybe offline if unvalidated check (arpping or ping) was older then "arp_soft_offline_device_timeout"
        # => validated means, the answer was from the expected ip and mac
        # => unvalidated means, the answer was from the excpected ip but different mac
        maybe_offline = unvalidated_last_seen_diff > self.config.arp_soft_offline_device_timeout or validated_last_seen_diff > self.config.arp_hard_offline_device_timeout

        # last check, if the device is really offline AND unvalidated check only allowed if validated check (arp-scan) is not older then "arp_hard_offline_device_timeout"
        # ping could be unvalidated, means it is only valid until "arp_hard_offline_device_timeout"
        ping_check = validated_last_seen_diff < self.config.arp_hard_offline_device_timeout
        
        outdated = validated_last_seen_diff > self.config.arp_clean_device_timeout
        
        return [outdated, maybe_offline, ping_check]

    def _checkDevice(self, device, force = False):
        mac = device.getMAC()
        
        stat = self.cache.getUnlockedDeviceStat(mac)
        if stat is None:
            logging.info("Can't check device {}. Stat is missing.".format(device))
            return
 
        if force:
            maybe_offline = True
            ping_check = True
        else:
            [outdated, maybe_offline, ping_check] = self._possibleOfflineStates(stat)
            
            if outdated:
                self._removeDevice(mac)
                return

            # State checke only for devices without DeviceChecker
            if mac in self.registered_devices and self.registered_devices[mac] is not None:
                return

        if maybe_offline:
            if device.getIP() is not None and ping_check:
                check_thread = threading.Thread(target=self._pingDevice, args=(device, stat, ))
                check_thread.start()
                return
                
            self._markDeviceAsOffline(device, stat)
    
    def _pingDevice(self, device, stat):
        startTime = datetime.now()
        
        try:
            methods = ["arping"]
            answering_mac = Helper.getMacFromArpPing(device.getIP(), self.config.main_interface, 10, self._isRunning)
            if answering_mac is None:
                methods.append("ping")
                answering_mac = Helper.getMacFromPing(device.getIP(), 5, self._isRunning)

            duration = round((datetime.now() - startTime).total_seconds(),2)
            if answering_mac is not None:
                validated = answering_mac == device.getMAC()
                self.cache.lock(self)
                logging.info("Device {} is {} online. Checked with {} in {} seconds".format(device,"validated" if validated else "unvalidated", " & ".join(methods),duration))
                self._refreshDevice(device, validated)
                self.cache.unlock(self)
                return
            
            [_, maybe_offline, ping_check] = self._possibleOfflineStates(stat)
            
            if maybe_offline or not ping_check:
                logging.info("Device {} is offline. Checked with {} in {} seconds".format(device," & ".join(methods),duration))
                self._markDeviceAsOffline(device, stat)

        except Exception as e:
            self.cache.cleanLocks(self)
            self._handleUnexpectedException(e, None, -1)
        
    def _markDeviceAsOffline(self, device, stat):
        if device.getIP() is not None:
            # check if there is another device with the same IP
            similarDevices = list(filter(lambda d: d.getMAC() != device.getMAC() and d.getIP() == device.getIP(), self.cache.getDevices() ))
            if len(similarDevices) > 0:
                self._removeDevice(device.getMAC())
                return
        
        if stat.isOnline():
            self.cache.lock(self)
            stat.lock(self)
            stat.setOnline(False)
            self.cache.confirmStat( self, stat )
            self.cache.unlock(self)

    def _refreshDevice(self, device, validated):
        mac = device.getMAC()
        
        stat = self.cache.getDeviceStat(mac)
        stat.setLastSeen(validated)
        if validated:
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
    
    def _removeDevice(self,mac):
        self.cache.lock(self)
        self.cache.removeDevice(self, mac)
        self.cache.removeDeviceStat(self, mac)
        if self.registered_devices[mac] is not None:
            self.registered_devices[mac].terminate()
            del self.registered_devices[mac]
        self.cache.unlock(self)

    def getEventTypes(self):
        return [ 
            { "types": [Event.TYPE_DEVICE], "actions": [Event.ACTION_CREATE,Event.ACTION_MODIFY], "details": None }
        ]

    def processEvents(self, events):
        disabled_devices = []
        unregistered_devices = []
        unvalidated_devices = []
        
        for event in events:
            device = event.getObject()

            connection = device.getConnection()
            if event.hasDetail("connection") and (connection is None or not connection.isEnabled()):
                disabled_devices.append(device)
            elif device.getMAC() not in self.registered_devices:
                unregistered_devices.append(device)
                
        if len(disabled_devices) > 0:
            for device in set(disabled_devices):
                logging.info("Recheck device {}".format(device))
                self._checkDevice(device, True)
        
        if len(unregistered_devices) > 0:
            self.cache.lock(self)
            for device in set(unregistered_devices):
                logging.info("Register lazy device {}".format(device))
                self._refreshDevice(device, False)
            self.cache.unlock(self)
            
