import threading
import socket
import traceback

from datetime import datetime, timedelta
import time
import re
import math
import logging

from lib.scanner.handler import _handler

from lib.scanner.dto.device import Device
from lib.scanner.dto.event import Event

from lib.scanner.helper import Helper
        
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
                            self.cache.confirmDevice( self.arpscanner, device )

                            stat = self.cache.getDeviceStat(client_mac)
                            stat.setLastSeen(True)
                            self.cache.confirmStat( self.arpscanner, stat )

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
        
        self.last_cleanup = {}

        self.dhcp_listener = DHCPListener(self, self.cache, self.config.main_interface)

    def start(self):
        self.dhcp_listener.start()
        
        super().start()

    def terminate(self):
        self.dhcp_listener.terminate()
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
                    collected_arps = []
                    for network in ipv4_networks:
                        arp_result = Helper.arpscan(self.config.main_interface, network, self._isRunning)
                        for arp_data in arp_result:
                            ip = arp_data["ip"]
                            mac = arp_data["mac"]
                            info = arp_data["info"]
                            dns = self.cache.nslookup(ip)
                            collected_arps.append([ip, mac, dns, info])
                except Exception as e:
                    if not self.is_running:
                        break
                    raise e

                try:
                    self.cache.lock(self)

                    processed_macs = {}
                    for [ip, mac, dns, info] in collected_arps:
                        device = self.cache.getDevice(mac)
                        device.setIP("arpscan", 1, ip)
                        device.setDNS("nslookup", 1, dns)
                        device.setInfo(info)
                        self.cache.confirmDevice( self, device )

                        stat = self.cache.getDeviceStat(mac)
                        stat.setLastSeen(True)
                        self.cache.confirmStat( self, stat )

                        processed_macs[mac] = ip
                        #processed_ips[ip] = mac

                    device = self.cache.getDevice(server_mac)
                    device.setIP("arpscan", 1, self.config.server_ip)
                    device.setDNS("nslookup", 1, self.config.server_domain)
                    device.setInfo(self.config.server_name)
                    self.cache.confirmDevice( self, device )

                    stat = self.cache.getDeviceStat(server_mac)
                    stat.setLastSeen(True)
                    self.cache.confirmStat( self, stat )

                    processed_macs[server_mac] = self.config.server_ip

                    for device in self.cache.getDevices():
                        if device.getMAC() in processed_macs:
                            continue

                        if device.getIP() is None:
                            self._initDeviceIP(device, lambda d: self._cleanDeviceLazy(d), lambda d: self._cleanDeviceLazy(d) )
                        else:
                            self._cleanDevice(device)

                    self.cache.unlock(self)
                except Exception as e:
                    self.cache.cleanLocks(self)
                    self._handleUnexpectedException(e)

            suspend_timeout = self._getSuspendTimeout()
            if suspend_timeout > 0:
                timeout = suspend_timeout
            else:
                timeout = self.config.arp_scan_interval
                        
            self._wait(timeout)

    def _cleanDeviceLazy(self, device):
        try:
            self.cache.lock(self)
            self._cleanDevice(device)
            self.cache.unlock(self)
        except Exception as e:
            self.cache.cleanLocks(self)

    def _cleanDevice(self, device):
        mac = device.getMAC()
        
        stat = self.cache.getUnlockedDeviceStat(mac)
        if stat is None:
            logging.info("Can't check device {}. Stat is missing.".format(device))
            return

        now = datetime.now()

        if ( now - stat.getUnvalidatedLastSeen() ).total_seconds() > self.config.arp_clean_timeout:
            self.cache.removeDevice(self, mac)
            self.cache.removeDeviceStat(self, mac)
            return

        # UserIP's should be delegated to DeviceChecker
        if device.getIP() in self.config.user_devices:
            return

        if stat.isOnline() and ( stat.getValidatedLastSeen() is None or ( now - stat.getValidatedLastSeen() ).total_seconds() > self.config.arp_offline_timeout ):
            if device.getIP() is None:
                stat.lock(self)
                stat.setOffline()
                self.cache.confirmStat( self, stat )
            else:
                if mac not in self.last_cleanup or (now - self.last_cleanup[mac]).total_seconds() > self.config.arp_offline_timeout:
                    self.last_cleanup[mac] = now
                    self._pingDevice(device, "cleanup", True)

    def _processDevice(self, device):
        # UserIP's should be delegated to DeviceChecker
        if device.getIP() in self.config.user_devices:
            return

        self._pingDevice(device, "init", False)

    def _pingDevice(self, device, reason, long_check):
        #if device.getIP() is None:
        #    raise Exception("test")
        #    logging.error("Device {} has no IP. Ping skipped [{}]".format(device, reason)) # should never happen
        if device.getMAC() in self.config.silent_device_macs:
            logging.info("Device {} is a silent device. Ping skipped [{}]".format(device, reason))
        else:
            check_thread = threading.Thread(target=self._pingDeviceJob, args=(device, reason, long_check))
            check_thread.start()
    
    def _pingDeviceJob(self, device, reason, long_check):
        try:
            startTime = datetime.now()

            methods = ["arping"]
            answering_mac = Helper.getMacFromArpPing(device.getIP(), self.config.main_interface, 20 if long_check else 10, self._isRunning)
            if answering_mac is None:
                methods.append("ping")
                answering_mac = Helper.getMacFromPing(device.getIP(), 20 if long_check else 10, self._isRunning)

            duration = round((datetime.now() - startTime).total_seconds(),2)

            self.cache.lock(self)

            if answering_mac is not None:
                if answering_mac != device.getMAC():
                    logging.info("Device {} has wrong ip. Answering MAC was {} after {} seconds [{}]".format(device, answering_mac, duration, reason))
                    device.lock(self)
                    device.clearIP()
                    device.unlock(self)
                    stat = self.cache.getDeviceStat(device.getMAC())
                    stat.setOffline()
                    self.cache.confirmStat( self, stat )
                else:
                    logging.info("Device {} is online. Checked with {} in {} seconds [{}]".format(device, " & ".join(methods), duration, reason))
                    stat = self.cache.getDeviceStat(device.getMAC())
                    stat.setLastSeen(True)
                    self.cache.confirmStat( self, stat )
            else:
                #if long_check:
                logging.info("Device {} is offline. Checked with {} in {} seconds [{}]".format(device, " & ".join(methods), duration, reason))
                stat = self.cache.getDeviceStat(device.getMAC())
                stat.setOffline()
                self.cache.confirmStat( self, stat )

            self.cache.unlock(self)

        except Exception as e:
            self.cache.cleanLocks(self)
            self._handleUnexpectedException(e, None, -1)

    def _initDeviceIP(self, device, success_callback, failure_callback = None):
        check_thread = threading.Thread(target=self._initDeviceIPJob, args=(device, success_callback, failure_callback,))
        check_thread.start()

    def _initDeviceIPJob(self, device, success_callback, failure_callback):
        ip_address = Helper.getIPFromArpTable(device.getMAC())
        if ip_address is None:
            if failure_callback is not None:
                failure_callback(device)
            return

        self.cache.lock(self)

        device.lock(self)
        dns = self.cache.nslookup(ip_address)
        device.setIP("arpscan", 1, ip_address)
        device.setDNS("nslookup", 1, dns)
        self.cache.confirmDevice( self, device )

        self.cache.unlock(self)

        success_callback(device)

    def getEventTypes(self):
        return [ 
            { "types": [Event.TYPE_DEVICE], "actions": [Event.ACTION_CREATE,Event.ACTION_MODIFY], "details": None }
        ]

    def processEvents(self, events):
        changed_devices = {}

        for event in events:
            if event.getAction() == Event.ACTION_CREATE:
                if event.hasDetail("ip"):
                    continue

                device = event.getObject()
                if device.getIP() is not None:
                    continue

                self._initDeviceIP(device, lambda d: self._processDevice(d) )
            else:
                if not event.hasDetail("connection"):
                    continue

                device = event.getObject()
                if device.getIP() is not None:
                    continue

                detail = event.getDetail("connection")
                if Device.EVENT_DETAIL_CONNECTION_DISABLE in detail:
                    self.cache.lock(self)
                    stat = self.cache.getDeviceStat(device.getMAC())
                    stat.setOffline()
                    self.cache.confirmStat( self, stat )
                    self.cache.unlock(self)
                continue
