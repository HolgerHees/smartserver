import threading
import requests
from urllib3.exceptions import InsecureRequestWarning
import logging
from datetime import datetime

from fritzconnection import FritzConnection
from fritzconnection.lib.fritzhosts import FritzHosts

from lib.handler import _handler
from lib.dto.device import Connection


class Fritzbox(_handler.Handler): 
    def __init__(self, config, cache ):
        super().__init__()
      
        self.config = config
        self.cache = cache
        
        self.is_running = True
        
        self.sessions = {}
        
        self.fritzbox_refreshed = {}
        self.fritzbox_devices = {}
        
        self.fc = {}
        self.fh = {}
        for fritzbox_device_ip in self.config.fritzbox_devices:
            self.fc[fritzbox_device_ip] = FritzConnection(address=fritzbox_device_ip, user=self.config.fritzbox_username, password=self.config.fritzbox_password)
            self.fh[fritzbox_device_ip] = FritzHosts(address=fritzbox_device_ip, user=self.config.fritzbox_username, password=self.config.fritzbox_password)
        
        self.condition = threading.Condition()
        self.thread = threading.Thread(target=self.checkFritzbox, args=())
        
        requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

    def start(self):
        self.thread.start()
        
    def terminate(self):
        with self.condition:
            self.is_running = False
            self.condition.notifyAll()
            
    def checkFritzbox(self):
        
        for fritzbox_device_ip in self.config.fritzbox_devices:
            self.fritzbox_devices[fritzbox_device_ip] = {}
        
        while self.is_running:
            
            events = []

            timeout = 60
            
            now = datetime.now().timestamp()
            for fritzbox_device_ip in self.config.fritzbox_devices:
                self._processDevice(fritzbox_device_ip, now, events)

            if len(events) > 0:
                self._getDispatcher().dispatch(self,events)

            if timeout > 0:
                with self.condition:
                    self.condition.wait(timeout)
                    
    def _processDevice(self, fritzbox_ip, now, events):
        fritzbox_mac = self.cache.ip2mac(fritzbox_ip)
        if fritzbox_mac is None:
            raise NetworkException()
        
        #https://github.com/blackw1ng/FritzBox-monitor/blob/master/checkfritz.py
        
        link_state = self.fc[fritzbox_ip].call_action("WANCommonInterfaceConfig1", "GetCommonLinkProperties")
        #{'NewWANAccessType': 'Ethernet', 'NewLayer1UpstreamMaxBitRate': 1000000, 'NewLayer1DownstreamMaxBitRate': 1000000, 'NewPhysicalLinkStatus': 'Up'}
        #traffic_state = self.fc[fritzbox_ip].call_action("LANEthernetInterfaceConfig1", "GetStatistics")
        #{'NewBytesSent': 513185675, 'NewBytesReceived': 488698598, 'NewPacketsSent': 1990181, 'NewPacketsReceived': 4184644}
        #wan_traffic_state_out = self.fc[fritzbox_ip].call_action("WANCommonInterfaceConfig1", "GetTotalBytesSent")
        #{'NewTotalBytesSent': 322724083}
        #wan_traffic_state_in = self.fc[fritzbox_ip].call_action("WANCommonInterfaceConfig1", "GetTotalBytesReceived")
        #{'NewTotalBytesReceived': 1141904910}
        
        _traffic_state = self.fc[fritzbox_ip].call_action("WANCommonIFC1", "GetAddonInfos")
        traffic_state = {'sent': int(_traffic_state["NewX_AVM_DE_TotalBytesSent64"]), 'received': int(_traffic_state["NewX_AVM_DE_TotalBytesReceived64"])}
        
        #logging.info(self.fc[fritzbox_ip].call_action("WANCommonInterfaceConfig1", "GetTotalBytesSent"))
        #logging.info(self.fc[fritzbox_ip].call_action("WANCommonInterfaceConfig1", "GetTotalBytesReceived"))
        #logging.info(self.fc[fritzbox_ip].call_action("WANEthernetLinkConfig1", "GetEthernetLinkStatus"))
        #logging.info(self.fc[fritzbox_ip].call_action("WANIPConnection1", "GetInfo"))
        #logging.info(self.fc[fritzbox_ip].call_action("WANCommonIFC1", "GetInfo"))
        
        self.cache.lock()

        fritzbox_device = self.cache.getDevice(fritzbox_mac)
        fritzbox_device.setIP(fritzbox_ip)
        self.cache.confirmDevice( fritzbox_device, lambda event: events.append(event) )
        
        stat = self.cache.getStat(fritzbox_mac)
        stat.setDetail("wan_type",link_state["NewWANAccessType"], "string")
        stat.setDetail("wan_state",link_state["NewPhysicalLinkStatus"], "string")

        if fritzbox_mac in self.fritzbox_refreshed:
            in_bytes = stat.getInBytes()
            if in_bytes > 0:
                time_diff = now - self.fritzbox_refreshed[fritzbox_mac]
                byte_diff = traffic_state["received"] - in_bytes
                if byte_diff > 0:
                    stat.setInAvg(byte_diff / time_diff)
                
            outBytes = stat.getOutBytes()
            if outBytes > 0:
                time_diff = now - self.fritzbox_refreshed[fritzbox_mac]
                byte_diff = traffic_state["sent"] - outBytes
                if byte_diff > 0:
                    stat.setOutAvg(byte_diff / time_diff)
       
        stat.setInBytes(traffic_state["received"])
        stat.setOutBytes(traffic_state["sent"])
        stat.setInSpeed(link_state["NewLayer1DownstreamMaxBitRate"] * 1000)
        stat.setOutSpeed(link_state["NewLayer1UpstreamMaxBitRate"] * 1000)
        self.cache.confirmStat( stat, lambda event: events.append(event) )
                
        self.cache.unlock()

        self.fritzbox_refreshed[fritzbox_mac] = now

        #https://fritzconnection.readthedocs.io/en/1.9.1/sources/library.html#fritzhosts

        #hosts = self.fc[fritzbox_ip].get_active_hosts()
        
        #self.cache.lock()

        #_active_client_macs = []
        #for index, host in enumerate(hosts, start=1):
        #    if host["ip"] == fritzbox_ip:
        #        continue
            
        #    device = self.cache.getDevice(host["mac"])
        #    device.setIP(host["ip"])
        #    #device.addHopConnection(Connection.VIRTUAL, self.config.default_vlan, fritzbox_mac, "lan", fritzbox_device);
        #    self.cache.confirmDevice( device, lambda event: events.append(event) )
        #    #{'ip': '192.168.0.107', 'name': 'AP-Haus', 'mac': 'D0:21:F9:6D:91:4D', 'status': True, 'interface_type': 'Ethernet', 'address_source': 'DHCP', 'lease_time_remaining': 0}
            
        #    _active_client_macs.append(host["mac"])
        #    self.fritzbox_devices[fritzbox_ip][host["mac"]] = [ host["mac"], self.config.default_vlan, fritzbox_mac, "lan" ]
            
        #for [ mac, vlan, target_mac, target_interface ] in list(self.fritzbox_devices[fritzbox_ip].values()):
        #    if mac not in _active_client_macs:
        #        #device = self.cache.getDevice(mac)
        #        # connection should still exists, also when device becomes offline
        #        #device.removeHopConnection(vlan, target_mac, target_interface)
        #        #self.cache.confirmDevice( device, lambda event: events.append(event) )
                
        #        del self.fritzbox_devices[fritzbox_ip][mac]
        
        #self.cache.unlock()
       
