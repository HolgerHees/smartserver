import threading
import requests
from urllib3.exceptions import InsecureRequestWarning
import logging
from datetime import datetime
import traceback

from fritzconnection import FritzConnection
from fritzconnection.lib.fritzhosts import FritzHosts
from fritzconnection.lib.fritzwlan import FritzWLAN
from fritzconnection.core.exceptions import FritzLookUpError
from fritzconnection.core.exceptions import FritzConnectionException
from fritzconnection.core.exceptions import FritzServiceError

from lib.handler import _handler
from lib.dto.device import Connection
from lib.dto.group import Group
from lib.dto.event import Event


class Fritzbox(_handler.Handler): 
    def __init__(self, config, cache ):
        super().__init__()
      
        self.config = config
        self.cache = cache
        
        self.is_running = True
        
        self.sessions = {}
        
        self.next_run = {}
        
        self.has_wifi_networks = False
        self.wifi_networks = {}

        self.wifi_associations = {}
        self.wifi_clients = {}
        
        self.dhcp_clients = {}
        
        self.known_clients = {}
        self.fritzbox_macs = {}
        
        #self.uid_macs_map = {}
        #self.uid_child_mac_map = {}
        #self.child_mac_parent_mac_map = {}
        
        self.devices = {}

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
        
        self.delayed_lock = threading.Lock()
        self.delayed_devices = {}
        self.delayed_wakeup_timer = None
        
        requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

    def start(self):
        self.thread.start()
        
    def terminate(self):
        with self.condition:
            self.is_running = False
            self.condition.notifyAll()
            
    def _checkFritzbox(self):
        was_suspended = {}
        
        now = datetime.now().timestamp()
        
        for fritzbox_ip in self.config.fritzbox_devices:
            self.next_run[fritzbox_ip] = {"device": now, "mesh_topologie": now, "wifi_networks": now, "wifi_clients": now, "dhcp_clients": now}
            
            self.wifi_networks[fritzbox_ip] = {}
            
            self.wifi_associations[fritzbox_ip] = {}
            self.wifi_clients[fritzbox_ip] = {}
            
            self.dhcp_clients[fritzbox_ip] = {}
            
            self.known_clients[fritzbox_ip] = {}
            self.fritzbox_macs[fritzbox_ip] = None
            
            was_suspended[fritzbox_ip] = False
        
        while self.is_running:
            now = datetime.now().timestamp()
            
            events = []

            timeout = 60
            
            for fritzbox_ip in self.config.fritzbox_devices:
                try:
                    if was_suspended[fritzbox_ip]:
                        logging.warning("Resume Fritzbox '{}'.".format(fritzbox_ip))
                        was_suspended[fritzbox_ip] = False
                        
                    timeout = self._processDevice(fritzbox_ip, now, events, timeout)
                except FritzConnectionException as e:
                    logging.error("Fritzbox '{}' not accessible. Will suspend for 1 minutes.".format(fritzbox_ip))
                    logging.error(traceback.format_exc())
                    if timeout > 60:
                        timeout = 60
                    was_suspended[fritzbox_ip] = True
                except Exception as e:
                    self.cache.cleanLocks(self, events)

                    logging.error("Fritzbox '{}' got unexpected exception. Will suspend for 15 minutes.".format(fritzbox_ip))
                    logging.error(traceback.format_exc())
                    if timeout > self.config.remote_error_timeout:
                        timeout = self.config.remote_error_timeout
                    was_suspended[fritzbox_ip] = True
                    
            if len(events) > 0:
                self._getDispatcher().dispatch(self,events)

            if timeout > 0:
                with self.condition:
                    self.condition.wait(timeout)
                    
    def _processDevice(self, fritzbox_ip, now, events, timeout):
        #https://fritzconnection.readthedocs.io/en/1.9.1/sources/library.html#fritzhosts

        #if self.next_run[fritzbox_ip]["mesh_topologie"] <= now:
        #    [timeout, self.next_run[fritzbox_ip]["mesh_topologie"]] = self._fetchMesh(fritzbox_ip, now, timeout, self.config.fritzbox_network_interval)
       
        # needs to run first to find fritzbox mac on startup
        if self.next_run[fritzbox_ip]["dhcp_clients"] <= now:
            [timeout, self.next_run[fritzbox_ip]["dhcp_clients"]] = self._fetchDHCPClients(fritzbox_ip, now, events, timeout, self.config.fritzbox_client_interval)

        # needs to run before _fetchWifiClients, because of created groups which are used later
        if self.next_run[fritzbox_ip]["wifi_networks"] <= now:
            [timeout, self.next_run[fritzbox_ip]["wifi_networks"]] = self._fetchWifiNetworks(fritzbox_ip, now, events, timeout, self.config.fritzbox_network_interval)

        if self.next_run[fritzbox_ip]["wifi_clients"] <= now:
            [timeout, self.next_run[fritzbox_ip]["wifi_clients"]] = self._fetchWifiClients(fritzbox_ip, now, events, timeout, self.config.fritzbox_client_interval)

        if self.next_run[fritzbox_ip]["device"] <= now:
            [timeout, self.next_run[fritzbox_ip]["device"]] = self._fetchDeviceInfo(fritzbox_ip, now, events, timeout, self.config.fritzbox_client_interval)
                
        return timeout
    
    #def _fetchMesh(self, fritzbox_ip, now, global_timeout, call_timeout):
    #    logging.info("FETCH TOPOLOGIE {}".format(fritzbox_ip))
            
    #    _mesh_links = {}
    #    _mesh_devices = {}
    #    uid_macs_map = {}
    #    topologie = self.fh[fritzbox_ip].get_mesh_topology()
    #    for node in topologie["nodes"]:
    #        logging.info(node)
    #        #mac = node["device_mac_address"].lower()
    #        wifi_links = []
    #        node_macs = [node["device_mac_address"].lower()]
    #        for node_interface in node["node_interfaces"]:
    #            node_macs.append(node_interface["mac_address"].lower())
    #            if len(node_interface["node_links"]) == 0:
    #                continue
    #            #logging.info("    INTERFACE: {}-{}-{}".format(node_interface["name"], node_interface["type"], node_interface["mac_address"]))
    #            for node_link in node_interface["node_links"]:
    #                if node_link["uid"] not in _mesh_links:
    #                    _mesh_links[node_link["uid"]] = []
    #                _mesh_links[node_link["uid"]].append(node["uid"])
                    
    #                if node_interface["type"] == "WLAN":
    #                    wifi_links.append(node_link["uid"])
    #                    #logging.info("        LINK: {}".format(node_link["uid"]))
    #        _mesh_devices[node["uid"]] = [node,wifi_links]

    #        if node["is_meshed"]:
    #            uid_macs_map[node["uid"]] = list(set(node_macs))
    #        #mesh_macs[node["device_mac_address"].lower()] = node["uid"]
        
    #    uid_child_mac_map = {}
    #    for [node,wifi_links] in _mesh_devices.values():
    #        logging.info("DEVICE: {}-{}-{} (MESHED: {}-{})".format(node["uid"],node["device_name"],wifi_links,node["is_meshed"],node["mesh_role"]))
    #        for _link_uid in wifi_links:
    #            #logging.info("DEVICE: {}-{}-{} (MESHED: {}-{})".format(node["uid"],node["device_name"],node_macs,node["is_meshed"],node["mesh_role"]))
    #            linked_node_uids = list(filter(lambda uid: uid != node["uid"],_mesh_links[_link_uid]))
    #            if len(linked_node_uids) != 1:
    #                logging.error("Unexpected uid count")
    #                continue
    #            [linked_node,_] = _mesh_devices[linked_node_uids[0]]
    #            if linked_node["is_meshed"] and node["mesh_role"] != "master":
    #                if linked_node_uids[0] not in uid_child_mac_map:
    #                    uid_child_mac_map[linked_node_uids[0]] = []
    #                uid_child_mac_map[linked_node_uids[0]].append(node["device_mac_address"].lower())
                    
    #    self.uid_child_mac_map = uid_child_mac_map
    #    self.uid_macs_map = uid_macs_map
            
    #    if global_timeout > call_timeout:
    #        global_timeout = call_timeout

    #    return [global_timeout, now + call_timeout]
                
    def _fetchDHCPClients(self, fritzbox_ip, now, events, global_timeout, call_timeout ):
        first_run = not self.known_clients[fritzbox_ip]

        # collect devices which are not processed or which are outdated
        devices = self.cache.getDevices()
        new_clients = {}
        outdated_clients = {}
        for device in devices:
            mac = device.getMAC()
            if mac not in self.dhcp_clients[fritzbox_ip]:
                new_clients[mac] = device
            elif now - self.dhcp_clients[fritzbox_ip][mac] >= self.config.fritzbox_network_interval:
                outdated_clients[mac] = device
            else:
                continue

        if first_run or new_clients or outdated_clients:
            # check mac is not in known_clients or if known_clients is outdated
            reload_clients = outdated_clients.copy()
            for mac in new_clients:
                if mac not in self.known_clients[fritzbox_ip]:
                    reload_clients[mac] = new_clients[mac]
            
            if first_run or reload_clients:
                # fetch full list
                if first_run or len(reload_clients.keys()) > 5:
                    start = datetime.now().timestamp()
                    _hosts = {}
                    for _host in self.fh[fritzbox_ip].get_generic_host_entries():
                        mac = _host["NewMACAddress"].lower()
                        _hosts[mac] = _host
                        if self.fritzbox_macs[fritzbox_ip] is None and _host["NewIPAddress"] == fritzbox_ip:
                            logging.info("Found {} for fritzbox {}".format(mac, fritzbox_ip))
                            self.fritzbox_macs[fritzbox_ip] = mac
                    self.known_clients[fritzbox_ip] = _hosts
                    logging.info("Full refresh in {} seconds".format(datetime.now().timestamp() - start))
                # for small amount of hosts, fetch individual data
                else:
                    start = datetime.now().timestamp()
                    for mac in reload_clients:
                        try:
                            self.known_clients[fritzbox_ip][mac] = self.fh[fritzbox_ip].get_specific_host_entry(mac.upper())
                        except FritzLookUpError:
                            pass
                    logging.info("Partial refresh in {} seconds {}".format(datetime.now().timestamp() - start,list(reload_clients.values())))
    
            hosts = self.known_clients[fritzbox_ip]
    
            # clean unknown hosts
            for mac in list(new_clients.keys()):
                if mac not in hosts:
                    self.dhcp_clients[fritzbox_ip][mac] = now
                else:
                    outdated_clients[mac] = new_clients[mac]
                    
            # update known host devices
            if outdated_clients:
                self.cache.lock(self)
                for device in outdated_clients.values():
                    mac = device.getMAC()
                    device.lock(self)
                    if mac not in hosts:
                        logging.info("Removed details from {}".format(device))
                        device.removeIP("fritzbox-dhcp")
                        device.removeDNS("fritzbox-dhcp")
                    else:
                        host = hosts[mac]
                        #logging.info(host)
                        device.setIP("fritzbox-dhcp", 100, host["NewIPAddress"])
                        device.setDNS("fritzbox-dhcp", 100, host["NewHostName"])
                    self.cache.confirmDevice( device, lambda event: events.append(event) )
                        
                    self.dhcp_clients[fritzbox_ip][mac] = now
                self.cache.unlock(self)
                
        #self.uid_macs_map = {}
        #self.child_mac_parent_uid_map = {}
        #self.child_mac_parent_mac_map = {}
        
        #child_mac_parent_mac_map = {}
        #for uid in self.uid_macs_map:
        #    macs = self.uid_macs_map[uid]
        #    for mac in self.dhcp_clients[fritzbox_ip]:
        #        if mac in macs:
        #            logging.info("MAP {} => {}".format(uid,mac))
        #            child_macs = self.uid_child_mac_map[uid]
        #            for child_mac in child_macs:
        #                child_mac_parent_mac_map[child_mac] = mac
        #            break
                
        #for mac in child_mac_parent_mac_map.keys():
        #    logging.info("{} => {}".format(mac, child_mac_parent_mac_map[mac]))
            
        #self.child_mac_parent_mac_map = child_mac_parent_mac_map
            
        if global_timeout > call_timeout:
            global_timeout = call_timeout

        return [global_timeout, now + call_timeout]
        
    def _fetchWifiClients(self, fritzbox_ip, now, events, global_timeout, call_timeout ):
        fritzbox_mac = self.fritzbox_macs[fritzbox_ip]
        
        client_results = {}
        for gid in self.wifi_networks[fritzbox_ip]:
            index = self.wifi_networks[fritzbox_ip][gid]["index"]
            clients = self.fw[fritzbox_ip][index].get_hosts_info()
            client_results[gid] = clients
            #{'service': 1, 'index': 0, 'status': True, 'mac': '3C:61:05:DC:EA:C9', 'ip': '192.168.179.120', 'signal': 29, 'speed': 43}

        if client_results or self.wifi_associations[fritzbox_ip]:
            self.cache.lock(self)

            _active_client_macs = []
            _active_client_wifi_connections = []
            for gid in client_results:
                wlan_network = self.wifi_networks[fritzbox_ip][gid]

                for client in client_results[gid]:
                    mac = client["mac"].lower()
                    
                    logging.info(client)

                    if mac == self.cache.getGatewayMAC():
                        continue

                    target_mac = fritzbox_mac
                    target_interface = mac
                    vlan = self.config.default_vlan

                    uid = "{}-{}".format(mac, gid)

                    device = self.cache.getDevice(mac)
                    device.setIP("fritzbox-wifi", 99, client["ip"])
                    
                    #if mac in self.child_mac_parent_mac_map:
                    #    logging.info("REAL MAP {} => {}".format(mac,self.child_mac_parent_mac_map[mac]))
                    #    target_mac = self.child_mac_parent_mac_map[mac]

                    device.cleanDisabledHobConnections(target_mac, lambda event: events.append(event))
                    device.addHopConnection(Connection.WIFI, vlan, target_mac, target_interface);
                    device.addGID(gid)
                    self.cache.confirmDevice( device, lambda event: events.append(event) )

                    if not client["status"]: 
                        continue
                    
                    stat = self.cache.getConnectionStat(target_mac,target_interface)
                    stat.setInSpeed(client["speed"] * 1000000)
                    stat.setOutSpeed(client["speed"] * 1000000)
                    stat.setDetail("signal", client["signal"] * -1, "attenuation")
                    self.cache.confirmStat( stat, lambda event: events.append(event) )
                        
                    _active_client_macs.append(mac)
                    _active_client_wifi_connections.append(uid)
                    self.wifi_associations[fritzbox_ip][uid] = [ now, uid, mac, gid, vlan, target_mac, target_interface ]

            wifi_clients = {}
            for [ _, uid, mac, gid, vlan, target_mac, target_interface ] in list(self.wifi_associations[fritzbox_ip].values()):
                if uid not in _active_client_wifi_connections:
                    device = self.cache.getDevice(mac)
                    device.removeIP("fritzbox-wifi")
                    device.removeGID(gid)
                    # **** connection cleanup and stats cleanup happens in cleanDisabledHobConnection ****
                    device.disableHopConnection(Connection.WIFI, target_mac, target_interface)
                    self.cache.confirmDevice( device, lambda event: events.append(event) )
                    
                    del self.wifi_associations[fritzbox_ip][uid]
                else:
                    wifi_clients[mac] = now
            self.wifi_clients[fritzbox_ip] = wifi_clients
                        
            self.cache.unlock(self)
        
        if global_timeout > call_timeout:
            global_timeout = call_timeout

        return [global_timeout, now + call_timeout]
    
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
            self.cache.lock(self)

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
                    
            self.cache.unlock(self)
            
        has_wifi_networks = False
        for _fritzbox_ip in self.config.fritzbox_devices:
            if self.wifi_networks[_fritzbox_ip]:
                has_wifi_networks = True
                break
        self.has_wifi_networks = has_wifi_networks
            
        if global_timeout > call_timeout:
            global_timeout = call_timeout

        return [global_timeout, now + call_timeout]
            
    def _fetchDeviceInfo(self, fritzbox_ip, now, events, global_timeout, call_timeout ):
        fritzbox_mac = self.fritzbox_macs[fritzbox_ip]
        
        #https://github.com/blackw1ng/FritzBox-monitor/blob/master/checkfritz.py
        
        #_lan_link_state = self.fc[fritzbox_ip].call_action("LANEthernetInterfaceConfig1", "GetInfo")
        #lan_link_state = {'up': _lan_link_state["NewMaxBitRate"], 'down': _lan_link_state["NewMaxBitRate"], 'duplex': _lan_link_state["NewDuplexMode"]}

        try:
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

            self.cache.lock(self)

            fritzbox_device = self.cache.getUnlockedDevice(fritzbox_mac)
            if fritzbox_device is None or not fritzbox_device.hasIP("fritzbox"):
                fritzbox_device = self.cache.getDevice(fritzbox_mac)
                fritzbox_device.setIP("fritzbox", 100, fritzbox_ip)
                if fritzbox_mac == self.cache.getGatewayMAC():
                    fritzbox_device.addHopConnection(Connection.ETHERNET, self.config.default_vlan, self.cache.getWanMAC(), self.cache.getWanInterface() );
                self.cache.confirmDevice( fritzbox_device, lambda event: events.append(event) )
            
            stat = self.cache.getConnectionStat(fritzbox_mac, self.cache.getGatewayInterface(self.config.default_vlan))
            if fritzbox_ip in self.devices:
                in_bytes = stat.getInBytes()
                if in_bytes is not None:
                    time_diff = now - self.devices[fritzbox_ip]
                    byte_diff = lan_traffic_received - in_bytes
                    if byte_diff > 0:
                        stat.setInAvg(byte_diff / time_diff)
                    
                out_bytes = stat.getOutBytes()
                if out_bytes is not None:
                    time_diff = now - self.devices[fritzbox_ip]
                    byte_diff = lan_traffic_sent - out_bytes
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

                if fritzbox_ip in self.devices:
                    in_bytes = stat.getInBytes()
                    if in_bytes is not None:
                        time_diff = now - self.devices[fritzbox_ip]
                        byte_diff = wan_traffic_state["received"] - in_bytes
                        if byte_diff > 0:
                            stat.setInAvg(byte_diff / time_diff)
                        
                    out_bytes = stat.getOutBytes()
                    if out_bytes is not None:
                        time_diff = now - self.devices[fritzbox_ip]
                        byte_diff = wan_traffic_state["sent"] - out_bytes
                        if byte_diff > 0:
                            stat.setOutAvg(byte_diff / time_diff)
            
                stat.setInBytes(wan_traffic_state["received"])
                stat.setOutBytes(wan_traffic_state["sent"])
                stat.setInSpeed(wan_link_state["down"] * 1000)
                stat.setOutSpeed(wan_link_state["up"] * 1000)
                self.cache.confirmStat( stat, lambda event: events.append(event) )
                    
            self.cache.unlock(self)
            
            self.devices[fritzbox_ip] = now
        except FritzServiceError:
            logging.info("No LAN Device statistic available on '{}'. Check diabled.".format(fritzbox_ip))
            call_timeout = 99999999999999

        if global_timeout > call_timeout:
            global_timeout = call_timeout

        return [global_timeout, now + call_timeout]

    def _delayedWakeup(self):
        with self.delayed_lock:
            self.delayed_wakeup_timer = None
            
            missing_dhcp_macs = []
            missing_wifi_macs = []
            for mac in list(self.delayed_devices.keys()):
                for fritzbox_ip in self.config.fritzbox_devices:
                    if mac not in self.dhcp_clients[fritzbox_ip]:
                        missing_dhcp_macs.append(mac)
                    if self.has_wifi_networks and mac not in self.wifi_clients[fritzbox_ip] and self.delayed_devices[mac].supportsWifi():
                        missing_wifi_macs.append(mac)
                del self.delayed_devices[mac]
            
            triggered_types = {}
            for fritzbox_ip in self.next_run:
                if len(missing_dhcp_macs) > 0:
                    self.next_run[fritzbox_ip]["dhcp_clients"] = datetime.now().timestamp()
                    triggered_types["dhcp"] = True
                if len(missing_wifi_macs) > 0:
                    self.next_run[fritzbox_ip]["wifi_clients"] = datetime.now().timestamp()
                    triggered_types["wifi"] = True
                    
            if triggered_types:
                logging.info("Delayed trigger runs for {}".format(" & ".join(triggered_types)))

                with self.condition:
                    self.condition.notifyAll()
            else:
                logging.info("Delayed trigger not needed anymore")

    def getEventTypes(self):
        return [ 
            { "types": [Event.TYPE_DEVICE], "actions": [Event.ACTION_CREATE], "details": None },
            { "types": [Event.TYPE_DEVICE], "actions": [Event.ACTION_MODIFY], "details": ["online"] }
        ]

    def processEvents(self, events):
        with self.delayed_lock:
            has_new_devices = False
            for event in events:
                device = event.getObject()

                if event.getAction() == Event.ACTION_MODIFY and not self.has_wifi_networks or not device.supportsWifi():
                    continue
                
                logging.info("Delayed trigger started for {}".format(device))

                self.delayed_devices[device.getMAC()] = device
                has_new_devices = True

            if has_new_devices:
                if self.delayed_wakeup_timer is not None:
                    self.delayed_wakeup_timer.cancel()

                # delayed triggers try to group several event bulks into one
                self.delayed_wakeup_timer = threading.Timer(5,self._delayedWakeup)
                self.delayed_wakeup_timer.start()
