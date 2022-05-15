import threading
import socket
import traceback

from datetime import datetime, timedelta
import time
import re
import math
import logging

from smartserver import command

from lib.handler import _handler

from lib.dto._changeable import Changeable
from lib.dto.device import Device, Connection
from lib.dto.device_stat import DeviceStat
from lib.dto.event import Event

from lib.helper import Helper

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
                
        self.process = None
        
        self.event = threading.Event()

        #self.lastSeen = datetime(1, 1, 1, 0, 0)
        #self.lastPublished = datetime(1, 1, 1, 0, 0)
        
        #self.isOnline = None
      
    def run(self):
        logging.info("Device checker for {} started".format(self.device))
        is_supended = False
        
        while self.is_running:
            events = []

            try:
                if is_supended:
                    logging.warning("Resume DeviceChecker")
                    is_supended = False
                
                sleepTime = self.onlineSleepTime if self.stat.isOnline() else self.offlineSleepTime
                
                self.event.wait(sleepTime)
                self.event.clear()
                    
                if not self.is_running:
                    break
                
                timeout = self.onlineArpCheckTime if self.stat.isOnline() else self.offlineArpCheckTime
                arpRetries = self.onlineArpRetries if self.stat.isOnline() else self.offlineArpRetries
                    
                startTime = datetime.now()
                
                ip_address = self.device.getIP()
                mac_address = self.device.getMAC()
                address_family = AddressHelper.getAddressFamily(ip_address)
                
                loopIndex = 0
                while self.is_running:
                    if self.type != "android":
                        AddressHelper.knock(self.address_family,ip_address)
                        time.sleep(0.05)
                        
                    methods = ["arping"]
                    answering_mac = Helper.arpping(ip_address, self.interface, timeout)
                    if answering_mac is None and self.stat.isOnline():
                        methods.append("ping")
                        answering_mac = Helper.ping(ip_address, self.interface, timeout)
                        
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
                            self.cache.confirmStat( self.stat, lambda event: events.append(event) )
                            self.cache.unlock(self)
                        break
                        
                    loopIndex += 1
                    if loopIndex == arpRetries:
                        logging.info("Device {} is offline. Checked with {} in {} seconds".format(ip_address," & ".join(methods),duration))
                        if self.stat.isOnline():
                            self.cache.lock(self)
                            self.stat.lock(self)
                            self.stat.setOnline(False)
                            self.cache.confirmStat( self.stat, lambda event: events.append(event) )
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
                time.sleep(900)
        
    def terminate(self):
        if self.process != None:
            self.process.terminate()

        self.is_running = False
        self.event.set()

        logging.info("Terminate device checker for {}".format(self.device))
        
class DHCPListener(threading.Thread):
    def __init__(self, arpscanner, cache, interface):
        threading.Thread.__init__(self) 
        
        self.is_running = True

        self.arpscanner = arpscanner
        self.cache = cache
        
        self.interface = interface

    def run(self):
        logging.info("DHCP listener started")
        self.dhcpListenerProcess = Helper.dhcplisten(self.interface)
        if self.dhcpListenerProcess.returncode is not None:
            raise Exception("DHCP Listener not started")
            
        client_mac = None
        client_ip = None
        is_supended = False
        
        while self.is_running:
            output = self.dhcpListenerProcess.stdout.readline()
            self.dhcpListenerProcess.stdout.flush()
            if output == '' and self.dhcpListenerProcess.poll() is not None:
                if not self.is_running:
                    break
                raise Exception("DHCP Listener stoppen")
            
            if is_supended:
                logging.warning("Resume DHCPListener")
                is_supended = False
                
            if output:
                line = output.strip()
                if "BOOTP/DHCP" in line:
                    client_mac = None
                    client_ip = None
                else:
                    if line.startswith("Client-Ethernet-Address"):
                        match = re.search(r"^Client-Ethernet-Address ({})$".format("[a-z0-9]{2}:[a-z0-9]{2}:[a-z0-9]{2}:[a-z0-9]{2}:[a-z0-9]{2}:[a-z0-9]{2}"), line)
                        if match:
                            client_mac = match[1]
                        else:
                            logging.error("Can't parse Mac")
                            client_mac = None
                            
                    elif line.startswith("Requested-IP") and client_mac is not None:
                        match = re.search(r"^Requested-IP.*?({})$".format("[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}"), line)
                        if match:
                            client_ip = match[1]
                        else:
                            logging.error("Can't parse IP")
                            client_ip = None
                            continue
                            
                        events = []
                        
                        try:
                            client_dns = self.cache.nslookup(client_ip)
                            
                            self.cache.lock(self)
                            
                            device = self.cache.getDevice(client_mac)
                            device.setIP("dhcp_listener", 75, client_ip)
                            device.setDNS("nslookup", 1, client_dns)
                            self.cache.confirmDevice( device, lambda event: events.append(event) )
                            logging.info("New dhcp request for {}".format(device))
                            
                            self.arpscanner._refreshDevice( device, True, events )
                            
                            self.cache.unlock(self)
                            
                        except Exception as e:
                            self.cache.cleanLocks(self, events)
                            logging.error("DHCPListener checker got unexpected exception. Will suspend for 15 minutes.")
                            logging.error(traceback.format_exc())
                            is_supended = True
                        
                        if len(events) > 0:
                            self.arpscanner._dispatch(events)
                            
                        if is_supended:
                            time.sleep(900)
                        
                        client_mac = None
                        client_ip = None
                            
        rc = self.dhcpListenerProcess.poll()
        
    def terminate(self):
        self.is_running = False
        
        if self.dhcpListenerProcess != None:
            self.dhcpListenerProcess.terminate()

        logging.info("Terminate dhcp listener")

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
        
        while self._isRunning():
            try:
                collected_arps = self._fetchArpResult()
            except Exception as e:
                if not self.is_running:
                    break
                raise e

            events = []
            
            timeout = self.config.arp_scan_interval

            try:
                if self._isSuspended():
                    self._confirmSuspended()
                
                processed_ips = {}
                processed_macs = {}
                for [ip, mac, dns, info] in collected_arps:
                    if mac not in processed_macs:
                        if ip not in processed_ips:
                            info = re.sub("\s\\(DUP: [0-9]+\\)", "", info) # eleminate dublicate marker
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
                    self.cache.confirmDevice( device, lambda event: events.append(event) )
                                        
                    self._refreshDevice( device, True, events)
                    refreshed_macs.append(mac)
                                
                device = self.cache.getDevice(server_mac)
                device.setIP("arpscan", 1, self.config.server_ip)
                device.setDNS("nslookup", 1, self.config.server_domain)
                device.setInfo(self.config.server_name)
                self.cache.confirmDevice( device, lambda event: events.append(event) )
                    
                self._refreshDevice( device, True, events)
                refreshed_macs.append(server_mac)

                self.cache.unlock(self)

                for device in self.cache.getDevices():
                    if device.getMAC() in refreshed_macs:
                        continue
                    self._checkDevice(device, events)
            
            except Exception as e:
                self.cache.cleanLocks(self, events)
                timeout = self._handleUnexpectedException(e)

            if len(events) > 0:
                self._dispatch(events)

            if self._isSuspended():
                self._sleep(timeout)
            else:
                self._wait(timeout)
                
    def _fetchArpResult(self):
        collected_arps = []
        for network in self.config.networks:
            arp_result = Helper.arpscan(self.config.main_interface, network)
            for arp_data in arp_result:
                ip = arp_data["ip"]
                mac = arp_data["mac"]
                info = arp_data["info"]
                
                dns = self.cache.nslookup(ip)
                        
                collected_arps.append([ip, mac, dns, info])
        return collected_arps
                
    def _dispatch(self, events):
        self._getDispatcher().dispatch(self,events)

    def _checkDevice(self, device, events, force = False):
        mac = device.getMAC()
        
        stat = self.cache.getUnlockedDeviceStat(mac)
        if stat is None:
            logging.info("Can't check device {}. Stat is missing.".format(device))
            return
 
        now = datetime.now()
 
        if force:
            maybe_offline = True
            ping_check = True
        else:
            validated_last_seen_diff = (now - stat.getValidatedLastSeen()).total_seconds()

            if validated_last_seen_diff > self.config.arp_clean_device_timeout:
                self._removeDevice(mac, events)
                return

            # State checke only for devices without DeviceChecker
            if self.registered_devices[mac] is not None:
                return

            unvalidated_last_seen_diff = (now - stat.getUnvalidatedLastSeen()).total_seconds()
            
            # maybe offline if unvalidated check (arpping or ping) was older then "arp_soft_offline_device_timeout"
            # => validated means, the answer was from the expected ip and mac
            # => unvalidated means, the answer was from the excpected ip but different mac
            maybe_offline = unvalidated_last_seen_diff > self.config.arp_soft_offline_device_timeout or validated_last_seen_diff > self.config.arp_hard_offline_device_timeout

            # last check, if the device is really offline AND unvalidated check only allowed if validated check (arp-scan) is not older then "arp_hard_offline_device_timeout"
            # ping could be unvalidated, means it is only valid until "arp_hard_offline_device_timeout"
            ping_check = validated_last_seen_diff < self.config.arp_hard_offline_device_timeout

        if maybe_offline:
            if device.getIP() is not None and ping_check:
                check_thread = threading.Thread(target=self._pingDevice, args=(device, stat, ))
                check_thread.start()
                return
                
            self._markDeviceAsOffline(device, stat, events)
    
    def _pingDevice(self, device, stat):
        startTime = datetime.now()
        
        events = []
        try:
            methods = ["arping"]
            answering_mac = Helper.arpping(device.getIP(), self.config.main_interface, 10)
            if answering_mac is None:
                methods.append("ping")
                answering_mac = Helper.ping(device.getIP(), self.config.main_interface, 5)

            duration = round((datetime.now() - startTime).total_seconds(),2)
            if answering_mac is not None:
                validated = answering_mac == device.getMAC()
                logging.info("Device {} is {} online. Checked with {} in {} seconds".format(device,"validated" if validated else "unvalidated", " & ".join(methods),duration))
                self.cache.lock(self)
                self._refreshDevice(device, validated, events)
                self.cache.unlock(self)
                return

            logging.info("Device {} is offline. Checked with {} in {} seconds".format(device," & ".join(methods),duration))
            
            self._markDeviceAsOffline(device, stat, events)
        except Exception as e:
            self.cache.cleanLocks(self, events)
            self._handleUnexpectedException(e, None, -1)
            
        if len(events) > 0:
            self._dispatch(events)
        
    def _markDeviceAsOffline(self, device, stat, events):
        if device is not None and device.getIP() is not None:
            # check if there is another device with the same IP
            similarDevices = list(filter(lambda d: d.getMAC() != device.getMAC() and d.getIP() == device.getIP(), self.cache.getDevices() ))
            if len(similarDevices) > 0:
                self.cache.lock(self)
                self._removeDevice(device.getMAC(), events)
                self.cache.unlock(self)
                return
        
        if stat.isOnline():
            self.cache.lock(self)
            stat.lock(self)
            stat.setOnline(False)
            self.cache.confirmStat( stat, lambda event: events.append(event) )
            self.cache.unlock(self)
        

    def _refreshDevice(self, device, validated, events):
        mac = device.getMAC()
        
        stat = self.cache.getDeviceStat(mac)
        stat.setLastSeen(validated)
        stat.setOnline(True)
        self.cache.confirmStat( stat, lambda event: events.append(event) )
        
        if mac not in self.registered_devices:
            self.registered_devices[mac] = None
            
        if self.registered_devices[mac] is not None:
            return
        
        if device.getIP() in self.config.user_devices:
            user_config = self.config.user_devices[device.getIP()]
            self.registered_devices[mac] = DeviceChecker(self, self.cache, device, stat, self.config.main_interface, user_config["type"], user_config["timeout"])
            self.registered_devices[mac].start()
    
    def _removeDevice(self,mac, events):
        self.cache.removeDevice(mac, lambda event: events.append(event))
        self.cache.removeDeviceStat(mac, lambda event: events.append(event))
        if self.registered_devices[mac] is not None:
            self.registered_devices[mac].terminate()
            del self.registered_devices[mac]
            
    def getEventTypes(self):
        return [ 
            { "types": [Event.TYPE_DEVICE], "actions": [Event.ACTION_CREATE,Event.ACTION_MODIFY], "details": None }
        ]

    def processEvents(self, events):
        _events = []
        
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
            for device in disabled_devices:
                logging.info("Recheck device {}".format(device))
                self._checkDevice(device, events, True)
        
        if len(unregistered_devices) > 0:
            self.cache.lock(self)
            for device in unregistered_devices:
                logging.info("Register lazy device {}".format(device))
                self._refreshDevice(device, True, _events)
            self.cache.unlock(self)
            
        if len(_events) > 0:
            self._getDispatcher().dispatch(self, _events)
            
