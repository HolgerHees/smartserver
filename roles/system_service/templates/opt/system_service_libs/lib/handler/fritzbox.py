import threading
import requests
from urllib3.exceptions import InsecureRequestWarning
import logging
from datetime import datetime

from fritzconnection import FritzConnection
from fritzconnection.lib.fritzhosts import FritzHosts
from fritzconnection.lib.fritzwlan import FritzWLAN

from lib.handler import _handler
from lib.dto.device import Connection
from lib.dto.group import Group


class Fritzbox(_handler.Handler): 
    def __init__(self, config, cache ):
        super().__init__()
      
        self.config = config
        self.cache = cache
        
        self.is_running = True
        
        self.sessions = {}
        
        self.last_check = {}
        
        self.wifi_networks = {}
        self.wifi_clients = {}

        self.fc = {}
        self.fh = {}
        self.fw = {}
        for fritzbox_ip in self.config.fritzbox_devices:
            self.fc[fritzbox_ip] = FritzConnection(address=fritzbox_ip, user=self.config.fritzbox_username, password=self.config.fritzbox_password)
            self.fh[fritzbox_ip] = FritzHosts(address=fritzbox_ip, user=self.config.fritzbox_username, password=self.config.fritzbox_password)
            self.fw[fritzbox_ip] = {}
            self.fw[fritzbox_ip]["1"] = FritzWLAN(address=fritzbox_ip, service=1, user=self.config.fritzbox_username, password=self.config.fritzbox_password)
            self.fw[fritzbox_ip]["2"] = FritzWLAN(address=fritzbox_ip, service=2, user=self.config.fritzbox_username, password=self.config.fritzbox_password)
            self.fw[fritzbox_ip]["3"] = FritzWLAN(address=fritzbox_ip, service=3, user=self.config.fritzbox_username, password=self.config.fritzbox_password)
        
        self.condition = threading.Condition()
        self.thread = threading.Thread(target=self._checkFritzbox, args=())
        
        requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

    def start(self):
        self.thread.start()
        
    def terminate(self):
        with self.condition:
            self.is_running = False
            self.condition.notifyAll()
            
    def _checkFritzbox(self):
        for fritzbox_ip in self.config.fritzbox_devices:
            self.last_check[fritzbox_ip] = {"device": 0, "wifi_networks": 0, "wifi_clients": 0}
            self.wifi_networks[fritzbox_ip] = {}
            self.wifi_clients[fritzbox_ip] = {}
            
        while self.is_running:
            events = []

            timeout = 60
            
            now = datetime.now().timestamp()
            for fritzbox_ip in self.config.fritzbox_devices:
                try:
                    timeout = self._processDevice(fritzbox_ip, now, events, timeout)
                except NetworkException as e:
                    logging.warning("{}. Will retry in 15 seconds.".format(e))
                    if timeout > 15:
                        timeout = 15
                    
            if len(events) > 0:
                self._getDispatcher().dispatch(self,events)

            if timeout > 0:
                with self.condition:
                    self.condition.wait(timeout)
                    
    def _processDevice(self, fritzbox_ip, now, events, timeout):
        fritzbox_mac = self.cache.ip2mac(fritzbox_ip)
        if fritzbox_mac is None:
            raise NetworkException("Fritzbox '{}' currently not resolvable".format(fritzbox_ip))
        
        #https://fritzconnection.readthedocs.io/en/1.9.1/sources/library.html#fritzhosts

        if now - self.last_check[fritzbox_ip]["device"] >= self.config.fritzbox_client_interval:
            [timeout, self.last_check[fritzbox_ip]["device"]] = self._fetchDeviceInfo(fritzbox_mac, fritzbox_ip, now, events, timeout, self.config.fritzbox_client_interval)
                
        if now - self.last_check[fritzbox_ip]["wifi_networks"] >= self.config.fritzbox_network_interval:
            [timeout, self.last_check[fritzbox_ip]["wifi_networks"]] = self._fetchWifiNetworks(fritzbox_ip, now, events, timeout, self.config.fritzbox_network_interval)
        
        if now - self.last_check[fritzbox_ip]["wifi_clients"] >= self.config.fritzbox_client_interval:
            [timeout, self.last_check[fritzbox_ip]["wifi_clients"]] = self._fetchWifiClients(fritzbox_mac, fritzbox_ip, now, events, timeout, self.config.fritzbox_client_interval)
        
        return timeout
        
    def _fetchWifiClients(self, fritzbox_mac, fritzbox_ip, now, events, global_timeout, call_timeout ):
        client_results = {}
        for gid in self.wifi_networks[fritzbox_ip]:
            index = self.wifi_networks[fritzbox_ip][gid]["index"]
            clients = self.fw[fritzbox_ip][index].get_hosts_info()
            client_results[gid] = clients
            #{'service': 1, 'index': 0, 'status': True, 'mac': '3C:61:05:DC:EA:C9', 'ip': '192.168.179.120', 'signal': 29, 'speed': 43}

        if client_results or self.wifi_clients[fritzbox_ip]:
            self.cache.lock()

            _active_client_macs = []
            _active_client_wifi_connections = []
            for gid in client_results:
                wlan_network = self.wifi_networks[fritzbox_ip][gid]

                for client in client_results[gid]:
                    mac = client["mac"].lower()

                    if mac == self.cache.getGatewayMAC():
                        continue

                    target_mac = fritzbox_mac
                    target_interface = mac
                    vlan = self.config.default_vlan

                    uid = "{}-{}".format(mac, gid)

                    device = self.cache.getDevice(mac)
                    device.setIP(client["ip"])
                    device.addHopConnection(Connection.WIFI, vlan, target_mac, target_interface);
                    device.addGID(gid)
                    self.cache.confirmDevice( device, lambda event: events.append(event) )

                    if not client["status"]: 
                        continue
                    
                    stat = self.cache.getConnectionStat(target_mac,target_interface)
                    stat.setInSpeed(client["speed"] * 1000000)
                    stat.setOutSpeed(client["speed"] * 1000000)
                    stat.setDetail("signal", client["signal"], "attenuation")
                    self.cache.confirmStat( stat, lambda event: events.append(event) )
                        
                    _active_client_macs.append(mac)
                    _active_client_wifi_connections.append(uid)
                    self.wifi_clients[fritzbox_ip][uid] = [ now, uid, mac, gid, vlan, target_mac, target_interface ]

            for [ _, uid, mac, gid, vlan, target_mac, target_interface ] in list(self.wifi_clients[fritzbox_ip].values()):
                if uid not in _active_client_wifi_connections:
                    device = self.cache.getDevice(mac)
                    # connection should still exists, also when device becomes offline
                    #device.removeHopConnection(vlan, target_mac, target_interface)
                    device.removeGID(gid)
                    self.cache.confirmDevice( device, lambda event: events.append(event) )
                    
                    if mac not in _active_client_macs:
                        stat = self.cache.removeConnectionStat(target_mac, target_interface, lambda event: events.append(event))
                    
                    del self.wifi_clients[fritzbox_ip][uid]
                        
            self.cache.unlock()
        
        if global_timeout > call_timeout:
            global_timeout = call_timeout

        return [global_timeout, now]
    
    def _fetchWifiNetworks(self, fritzbox_ip, now, events, global_timeout, call_timeout ):
        _active_networks = {}
        for i in range(1,4):
            wifi_info = self.fw[fritzbox_ip][str(i)].get_info()
            if not wifi_info["NewEnable"]:
                continue

            gid = "{}-{}".format(fritzbox_ip,i)
            
            network = {
                "gid": gid,
                "index": str(i),
                "ssid": wifi_info["NewSSID"],
                "band": "5g" if i == 2 else "2g",
                "channel": wifi_info["NewChannel"]
            }
            
            _active_networks[gid] = network
            self.wifi_networks[fritzbox_ip][gid] = network
            
        if _active_networks or self.wifi_networks[fritzbox_ip]:
            self.cache.lock()

            for gid in _active_networks:
                network = _active_networks[gid]

                group = self.cache.getGroup(gid, Group.WIFI)
                group.setDetail("ssid", network["ssid"], "string")
                group.setDetail("band", network["band"], "string")
                group.setDetail("channel", network["channel"], "string")
                self.cache.confirmGroup(group, lambda event: events.append(event))
                        
            for gid in list(self.wifi_networks[fritzbox_ip].keys()):
                if gid not in _active_networks:
                    self.cache.removeGroup(gid, lambda event: events.append(event))
                    del self.wifi_networks[fritzbox_ip][gid]
                    
            self.cache.unlock()
            
        if global_timeout > call_timeout:
            global_timeout = call_timeout

        return [global_timeout, now]
            
    def _fetchDeviceInfo(self, fritzbox_mac, fritzbox_ip, now, events, global_timeout, call_timeout ):
        #https://github.com/blackw1ng/FritzBox-monitor/blob/master/checkfritz.py
        
        #_lan_link_state = self.fc[fritzbox_ip].call_action("LANEthernetInterfaceConfig1", "GetInfo")
        #lan_link_state = {'up': _lan_link_state["NewMaxBitRate"], 'down': _lan_link_state["NewMaxBitRate"], 'duplex': _lan_link_state["NewDuplexMode"]}

        _lan_traffic_state = self.fc[fritzbox_ip].call_action("LANEthernetInterfaceConfig1", "GetStatistics")
        lan_traffic_received = _lan_traffic_state["NewBytesReceived"]
        lan_traffic_sent = _lan_traffic_state["NewBytesSent"]
        
        if fritzbox_mac == self.cache.getGatewayMAC():
            _wan_link_state = self.fc[fritzbox_ip].call_action("WANCommonInterfaceConfig1", "GetCommonLinkProperties")
            wan_link_state = {'type': _wan_link_state["NewWANAccessType"], 'state': _wan_link_state["NewPhysicalLinkStatus"], 'up': _wan_link_state["NewLayer1UpstreamMaxBitRate"], 'down': _wan_link_state["NewLayer1DownstreamMaxBitRate"]}

            _wan_traffic_state = self.fc[fritzbox_ip].call_action("WANCommonIFC1", "GetAddonInfos")
            wan_traffic_state = {'sent': int(_wan_traffic_state["NewX_AVM_DE_TotalBytesSent64"]), 'received': int(_wan_traffic_state["NewX_AVM_DE_TotalBytesReceived64"])}
        
            lan_traffic_received += wan_traffic_state["received"]
            lan_traffic_sent += wan_traffic_state["sent"]

        self.cache.lock()

        fritzbox_device = self.cache.getDevice(fritzbox_mac)
        fritzbox_device.setIP(fritzbox_ip)
        if fritzbox_mac == self.cache.getGatewayMAC():
            fritzbox_device.addHopConnection(Connection.ETHERNET, self.config.default_vlan, self.cache.getWanMAC(), self.cache.getWanInterface() );
        self.cache.confirmDevice( fritzbox_device, lambda event: events.append(event) )
        
        stat = self.cache.getConnectionStat(fritzbox_mac, self.cache.getGatewayInterface(self.config.default_vlan))
        if self.last_check[fritzbox_ip]["device"] != 0:
            in_bytes = stat.getInBytes()
            if in_bytes > 0:
                time_diff = now - self.last_check[fritzbox_ip]["device"]
                byte_diff = lan_traffic_received - in_bytes
                if byte_diff > 0:
                    stat.setInAvg(byte_diff / time_diff)
                
            outBytes = stat.getOutBytes()
            if outBytes > 0:
                time_diff = now - self.last_check[fritzbox_ip]["device"]
                byte_diff = lan_traffic_sent - outBytes
                if byte_diff > 0:
                    stat.setOutAvg(byte_diff / time_diff)
       
        stat.setInBytes(lan_traffic_received)
        stat.setOutBytes(lan_traffic_sent)
        #stat.setInSpeed(lan_link_state['down'] * 1000)
        stat.setInSpeed(1000000000)
        #stat.setOutSpeed(lan_link_state['up'] * 1000)
        stat.setOutSpeed(1000000000)
        #stat.setDetail("duplex", "full" if _port["duplex"] == "fullDuplex" else "half", "string")
        #stat.setDetail("duplex", lan_link_state["duplex"], "string")
        self.cache.confirmStat( stat, lambda event: events.append(event) )

        if fritzbox_mac == self.cache.getGatewayMAC():
            stat = self.cache.getConnectionStat(self.cache.getWanMAC(),"wan")
            stat.setDetail("wan_type",wan_link_state["type"], "string")
            stat.setDetail("wan_state",wan_link_state["state"], "string")

            if self.last_check[fritzbox_ip]["device"] != 0:
                in_bytes = stat.getInBytes()
                if in_bytes > 0:
                    time_diff = now - self.last_check[fritzbox_ip]["device"]
                    byte_diff = wan_traffic_state["received"] - in_bytes
                    if byte_diff > 0:
                        stat.setInAvg(byte_diff / time_diff)
                    
                outBytes = stat.getOutBytes()
                if outBytes > 0:
                    time_diff = now - self.last_check[fritzbox_ip]["device"]
                    byte_diff = wan_traffic_state["sent"] - outBytes
                    if byte_diff > 0:
                        stat.setOutAvg(byte_diff / time_diff)
        
            stat.setInBytes(wan_traffic_state["received"])
            stat.setOutBytes(wan_traffic_state["sent"])
            stat.setInSpeed(wan_link_state["down"] * 1000)
            stat.setOutSpeed(wan_link_state["up"] * 1000)
            self.cache.confirmStat( stat, lambda event: events.append(event) )
                
        self.cache.unlock()

        if global_timeout > call_timeout:
            global_timeout = call_timeout

        return [global_timeout, now]

class NetworkException(Exception):
    pass
