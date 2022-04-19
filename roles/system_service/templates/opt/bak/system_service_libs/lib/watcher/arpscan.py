import threading
from datetime import datetime, timedelta
import re

from smartserver import command

from lib.watcher import watcher
from lib.dto.device import Device
from lib.dto.stats import Stats
from lib.dto.event import Event

from lib.helper import Helper


class ArpScanner(watcher.Watcher): 
    def __init__(self, logger, config, handler ):
        super().__init__(logger)
      
        self.logger = logger
        self.config = config
        self.handler = handler
        
        self.is_running = True
        self.last_refresh = 0
        
        self.arp_table = {}
        self.arp_check = {}
        self.arp_online = {}

        self.condition = threading.Condition()
        self.thread = threading.Thread(target=self.checkArpTable, args=())
        
        self.data_lock = threading.Lock()
        
    def start(self):
        self.thread.start()
        
    def terminate(self):
        with self.condition:
            self.is_running = False
            self.condition.notifyAll()
            
    def checkArpTable(self):
        dns_results = {}

        while self.is_running:
            changes = {}
            
            now = datetime.now()
            for network in self.config.networks:
                arp_result = Helper.arpscan(self.config.main_interface, network)

                processed_ips = {}
                processed_macs = []
                post_checked_macs = []

                for arp_data in arp_result:
                    ip = arp_data["ip"]
                    mac = arp_data["mac"]
                    info = arp_data["info"]
                    
                    if mac not in processed_macs:
                        if ip not in dns_results or (now - dns_results[ip][1]).total_seconds() > self.config.arp_scan_dns_interval:
                            dns = Helper.nslookup(ip)
                            dns_results[ip] = [dns,now]
                        else:
                            dns = dns_results[ip][0]
                        
                        arp = self._initArp(mac, ip, info, dns)
                        with self.data_lock:
                            if mac not in self.arp_table or not self.data_equal(self.arp_table[mac], arp):
                                self._appendChange(changes, Event.TYPE_DEVICE, mac, { "action": "change", "arp": arp })
                                self.arp_table[mac] = arp
                            
                            self.arp_check[mac] = now
                            if mac not in self.arp_online or not self.arp_online[mac]:
                                self.arp_online[mac] = True
                                self._appendChange(changes, Event.TYPE_DEVICE_STAT, mac, { "action": "change", "offline_since": None })

                        processed_macs.append(mac)
                    else:
                        # we have to check this mac separately
                        post_checked_macs.append(mac)
                    
                    if ip not in processed_ips:
                        processed_ips[ip] = mac
                    else:
                        # we have to check this mac separately
                        post_checked_macs.append(mac)
                        # and the related mac have to be checked too
                        post_checked_macs.append(processed_ips[ip])
                
            # FIXME double check for doublicate mac addresses or ips's
            #if len(post_checked_macs) > 0:
            #    for mac in list(set(post_checked_macs)):
            #        self.logger.info(mac)
                    
            mac = "00:00:00:00:00:00"
            try:
                with open("/sys/class/net/{}/address".format(self.config.main_interface), 'r') as f:
                    mac = f.read().strip()
            except (IOError, OSError) as e:
                pass
            
            ip = self.config.server_ip
            arp = self._initArp(mac, ip, self.config.server_name, self.config.server_domain)
            with self.data_lock:
                if mac not in self.arp_table or not self.data_equal(self.arp_table[mac], arp):
                    self._appendChange(changes, Event.TYPE_DEVICE, mac, { "action": "change", "arp": arp })
                    self.arp_table[mac] = arp
                
                self.arp_check[mac] = now
                if mac not in self.arp_online or not self.arp_online[mac]:
                    self.arp_online[mac] = True
                    self._appendChange(changes, Event.TYPE_DEVICE_STAT, mac, { "action": "change", "offline_since": None })
            
                for mac in list(self.arp_check.keys()):
                    if (now - self.arp_check[mac]).total_seconds() > self.config.arp_clean_device_timeout:
                        self.logger.info("Clean arp '{}' - '{}'".format(mac,self.arp_check[mac]["ip"]))
                        self._appendChange(changes, Event.TYPE_DEVICE, mac, { "action": "delete", "arp": self.arp_table[mac] })
                        self._appendChange(changes, Event.TYPE_DEVICE_STAT, mac, { "action": "delete", "offline_since": None })
                        del self.arp_check[mac]
                        del self.arp_table[mac]
                        del self.arp_online[mac]
                    elif (now - self.arp_check[mac]).total_seconds() > self.config.arp_offline_device_timeout:
                        self._appendChange(changes, Event.TYPE_DEVICE_STAT, mac, { "action": "change", "offline_since": self.arp_check[mac] })
                        self.arp_online[mac] = False
                    
            events = self._prepareEvents(changes)
            if len(events) > 0:
                self.last_refresh = round(datetime.now().timestamp(),3)
                self.handler.notify(self,events)

            with self.condition:
                self.condition.wait(self.config.arp_scan_interval)
                
    def triggerEvents(self, groups, devices, stats, events):
        for event in events:
            if event.getAction() != Event.ACTION_CREATE or event.getType() != Event.TYPE_DEVICE:
                continue
            
            with self.data_lock:
                mac = event.getIdentifier()

                if mac in self.arp_table:
                    continue

                _devices = list(filter(lambda d: d.getMAC() == mac, devices ))
                device = _devices[0]
                
                ip = device.getIP()
                
                self.logger.info("Register lazy device {}".format(device))
                self.arp_table[mac] = self._initArp(mac, ip, "", device.getDNS())
            
    def processEvents(self, groups, devices, stats, events):
        with self.data_lock:
            for event in events:
                mac = event.getIdentifier()
                
                if event.getType() == Event.TYPE_DEVICE_STAT:
                    mac = event.getIdentifier()

                    _devices = list(filter(lambda d: d.getMAC() == mac, devices ))
                    device = _devices[0] if len(_devices) > 0 else None
                    
                    if event.getPayload("action") == "delete":
                        for stat in list(filter(lambda d: d.getTarget() == mac, stats )):
                            stats.remove(stat)

                            self.logger.info("Clean stats {}".format(device if device else stat))
                            event.setAction(Event.ACTION_DELETE)
                    else:
                        _stats = list(filter(lambda d: d.getTarget() == mac, stats ))
                        if len(_stats) > 0:
                            stat = _stats[0]

                            self.logger.info("Update stats {}".format(device if device else stat))
                            event.setAction(Event.ACTION_MODIFY)
                        else:
                            # convert to create action for other listeners
                            stat = Stats(mac, "device")
                            stats.append(stat)
                        
                            self.logger.info("Add stats {}".format(device if device else stat))
                            event.setAction(Event.ACTION_CREATE)

                        stat.setOfflineSince( event.getPayload("offline_since") )
                else:
                    mac = event.getIdentifier()
                    
                    if event.getPayload("action") == "delete":
                        for device in list(filter(lambda d: d.getMAC() == mac, devices )):
                            devices.remove(device)

                            self.logger.info("Clean device {}".format(device))
                            event.setAction(Event.ACTION_DELETE)
                    else:
                        _arp_device = event.getPayload("arp")

                        _devices = list(filter(lambda d: d.getMAC() == mac, devices ))
                        if len(_devices) > 0:
                            device = _devices[0]
                            device.setIP(_arp_device["ip"])

                            self.logger.info("Update device {}".format(device))
                            event.setAction(Event.ACTION_MODIFY)
                        else:
                            device = Device(mac,"device")
                            device.setMAC(_arp_device["mac"])
                            device.setIP(_arp_device["ip"])
                            devices.append(device)

                            self.logger.info("Add device {}".format(device))
                            event.setAction(Event.ACTION_CREATE)

                        device.setInfo(_arp_device["name"])
                        device.setDNS(_arp_device["dns"].split(".")[0])

    def _initArp(self, mac, ip, name, dns):
        return {"mac": mac, "ip": ip, "name": name, "dns": dns }
