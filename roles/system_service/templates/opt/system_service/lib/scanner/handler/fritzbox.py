import threading
import requests
from urllib3.exceptions import InsecureRequestWarning
import logging
from datetime import datetime, timedelta

from fritzconnection import FritzConnection
from fritzconnection.lib.fritzhosts import FritzHosts
from fritzconnection.core.exceptions import FritzLookUpError
from fritzconnection.core.exceptions import FritzConnectionException
from fritzconnection.core.exceptions import FritzServiceError

from lib.scanner.handler import _handler
from lib.scanner.dto.device import Connection
from lib.scanner.dto.group import Group
from lib.scanner.dto.event import Event
from lib.scanner.helper import Helper


class Fritzbox(_handler.Handler): 
    def __init__(self, config, cache, fritzbox_devices ):
        super().__init__(config,cache)
        
        self.fritzbox_devices = fritzbox_devices

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
        
        self.delayed_lock = threading.Lock()
        self.delayed_dhcp_devices = {}
        self.delayed_wifi_devices = {}
        self.delayed_wakeup_timer = None

        requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

    def terminate(self):
        with self.delayed_lock:
            if self.delayed_wakeup_timer is not None:
                self.delayed_wakeup_timer.cancel()
        super().terminate()

    def _initNextRuns(self):
        now = datetime.now()
        for fritzbox_ip in self.fritzbox_devices.keys():
            self.next_run[fritzbox_ip] = {"device": now, "dhcp_clients": now, "mesh_clients": now}
        
    def _run(self):
        self._initNextRuns()

        for fritzbox_ip in self.fritzbox_devices.keys():
            self.wifi_networks[fritzbox_ip] = {}
            
            self.wifi_associations[fritzbox_ip] = {}
            self.wifi_clients[fritzbox_ip] = {}
            
            self.known_clients[fritzbox_ip] = {}
            self.dhcp_clients[fritzbox_ip] = {}
            
            self.fritzbox_macs[fritzbox_ip] = None

            self._setDeviceMetricState(fritzbox_ip, -1)
        
        for fritzbox_ip, fritzbox_device in self.fritzbox_devices.items():
            while self._isRunning():
                try:
                    self.fc[fritzbox_ip] = FritzConnection(address=fritzbox_ip, user=fritzbox_device["username"], password=fritzbox_device["password"])
                    self.fh[fritzbox_ip] = FritzHosts(address=fritzbox_ip, user=fritzbox_device["username"], password=fritzbox_device["password"])

                    self._setDeviceMetricState(fritzbox_ip, 1)
                    break
                except FritzConnectionException as e:
                    self._handleExpectedException("Fritzbox '{}' not accessible.".format(fritzbox_ip), fritzbox_ip)
                    self._wait(self._getSuspendTimeout(fritzbox_ip))

                    self._setDeviceMetricState(fritzbox_ip, 0)

            if not self._isRunning():
                break

        while self._isRunning():
            events = []

            for fritzbox_ip in self.fritzbox_devices.keys():
                try:
                    if self._isSuspended(fritzbox_ip):
                        continue
                        
                    self._processDevice(fritzbox_ip)

                    self._setDeviceMetricState(fritzbox_ip, 1)
                except FritzConnectionException as e:
                    self._initNextRuns()
                    self.cache.cleanLocks(self)

                    self._handleExpectedException("Fritzbox '{}' not accessible".format(fritzbox_ip), fritzbox_ip)
                    self._setDeviceMetricState(fritzbox_ip, 0)
                except Exception as e:
                    self._initNextRuns()
                    self.cache.cleanLocks(self)

                    self._handleUnexpectedException(e, fritzbox_ip)
                    self._setDeviceMetricState(fritzbox_ip, -1)

            timeout = 9999999999
            now = datetime.now()
            for fritzbox_ip in self.fritzbox_devices.keys():
                suspend_timeout = self._getSuspendTimeout(fritzbox_ip)
                if suspend_timeout > 0:
                    if suspend_timeout < timeout:
                        timeout = suspend_timeout
                else:
                    for next_run in self.next_run[fritzbox_ip].values():
                        diff = (next_run - now).total_seconds()
                        if diff < timeout:
                            timeout = diff
                            
            if timeout > 0:
                self._wait(timeout)
         
    def _processDevice(self, fritzbox_ip):
        #https://fritzconnection.readthedocs.io/en/1.9.1/sources/library.html#fritzhosts

        # needs to run first to find fritzbox mac on startup
        if self.next_run[fritzbox_ip]["dhcp_clients"] <= datetime.now():
            self._fetchDHCPClients(fritzbox_ip)

        if self.next_run[fritzbox_ip]["mesh_clients"] <= datetime.now():
            self._fetchMeshClients(fritzbox_ip)
                
        if self.next_run[fritzbox_ip]["device"] <= datetime.now():
            self._fetchDeviceInfo(fritzbox_ip)
    
    def _fetchMeshClients(self, fritzbox_ip):
        self.next_run[fritzbox_ip]["mesh_clients"] = datetime.now() + timedelta(seconds=self.config.fritzbox_client_interval)

        mesh_hops = {}
        #mesh_nodes = {}
        
        start = datetime.now().timestamp()
        topologie = self.fh[fritzbox_ip].get_mesh_topology()
        Helper.logProfiler(self, start, "Mesh data of '{}' fetched".format(fritzbox_ip))
        
        #logging.info(topologie)
        
        self.cache.lock(self)
        
        # ************ Prepare wifi networks ****************
        node_link_wifi_map = {}
        _active_networks = {}
        for node in topologie["nodes"]:
            for node_interface in node["node_interfaces"]:
                if node_interface["type"] != "WLAN":
                    continue
                
                if node_interface["ssid"]:
                    ssid = node_interface["ssid"]
                    channel = node_interface["current_channel"]
                    band = "5g" if channel > 13 else "2g"
                    priority = 1 if channel > 13 else 0
                    
                    gid = "{}-{}-{}".format(fritzbox_ip,band,ssid)
                    network = {
                        "gid": gid,
                        "ssid": ssid,
                        "band": band,
                        "priority": priority,
                        "vlan": self.config.default_vlan,
                        "channel": channel
                    }
                    self.wifi_networks[fritzbox_ip][gid] = network
                    _active_networks[gid] = network
                    
                    for node_link in node_interface["node_links"]:
                        node_link_wifi_map[node_link["uid"]] = network
                    
        if _active_networks or self.wifi_networks[fritzbox_ip]:
            for gid in _active_networks:
                network = _active_networks[gid]

                group = self.cache.getGroup(gid, Group.WIFI)
                group.setDetail("ssid", network["ssid"], "string")
                group.setDetail("band", network["band"], "string")
                group.setDetail("channel", network["channel"], "string")
                group.setDetail("priority", network["priority"], "hidden")
                self.cache.confirmGroup(self, group)
                        
            for gid in list(self.wifi_networks[fritzbox_ip].keys()):
                if gid not in _active_networks:
                    self.cache.removeGroup(self, gid)
                    del self.wifi_networks[fritzbox_ip][gid]
            
        has_wifi_networks = False
        for _fritzbox_ip in self.fritzbox_devices:
            if self.wifi_networks[_fritzbox_ip]:
                has_wifi_networks = True
                break
        self.has_wifi_networks = has_wifi_networks
        # ****************************************************
        
        # ************ Prepare wifi clients ****************
        for node in topologie["nodes"]:
            node_uid = node["uid"]
            mesh_type = node["mesh_role"] if node["is_meshed"] else None
            
            node_macs = [node["device_mac_address"].lower()]
            for node_interface in node["node_interfaces"]:
                node_macs.append(node_interface["mac_address"].lower())
            node_macs = list(set(node_macs))
            
            main_node_mac = None
            for node_mac in node_macs:
                if node_mac in self.dhcp_clients[fritzbox_ip]:
                    main_node_mac = node_mac
                    break
                
            if mesh_type is not None:
                if main_node_mac is None:
                    logging.warning(self.dhcp_clients[fritzbox_ip].keys())
                    logging.warning("No mac found for {} - {}".format(node_uid,node_macs))
                else:
                    mesh_hops[node_uid] = [main_node_mac,mesh_type]
                    
        _active_client_macs = []
        _active_associations = []
        for node in topologie["nodes"]:
            node_uid = node["uid"]
            
            for node_interface in node["node_interfaces"]:
                if node_interface["type"] != "WLAN":
                    continue

                if node_uid in mesh_hops and node_interface["opmode"] != "REPEATER":
                    continue

                for node_link in node_interface["node_links"]:
                    if node_link["state"] != "CONNECTED":
                        continue
                    
                    flip = node_link["node_1_uid"] == node_uid
                    source_key = "node_1_uid" if flip else "node_2_uid"
                    target_key = "node_2_uid" if flip else "node_1_uid"
                    
                    if node_link[target_key] in mesh_hops:
                        wifi_network = node_link_wifi_map[node_link["uid"]]
                        vlan = wifi_network["vlan"]
                        band = wifi_network["band"]
                        gid = wifi_network["gid"]

                        mac = mesh_hops[node_link[source_key]][0] if node_link[source_key] in mesh_hops else node_interface["mac_address"].lower()
                        target_mac = mesh_hops[node_link[target_key]][0]
                        target_interface = mac
                        
                        uid = "{}-{}-{}".format(mac, target_mac, gid)

                        connection_details = { "vlan": vlan, "gid": gid }

                        device = self.cache.getDevice(mac)
                        device.addHopConnection(Connection.WIFI, target_mac, target_interface, connection_details );
                        self.cache.confirmDevice( self, device )
                        
                        # mark as online for new clients or if it is not a user device (is checked in arpscan)
                        if mac not in self.wifi_clients[fritzbox_ip] or device.getIP() is None or device.getIP() not in self.config.user_devices:
                            stat = self.cache.getDeviceStat(mac)
                            stat.setLastSeen(False) # because no IP validation
                            stat.setOnline(True)
                            self.cache.confirmStat( self, stat )

                        stat = self.cache.getConnectionStat(target_mac,target_interface)
                        stat_data = stat.getData(connection_details)
                        stat_data.setInSpeed(node_link["cur_data_rate_rx"] * 1000)
                        stat_data.setOutSpeed(node_link["cur_data_rate_tx"] * 1000)
                        stat_data.setDetail("signal", node_link["rx_rcpi"], "attenuation")
                        if self.cache.confirmStat( self, stat ):
                            if device.hasMultiConnections():
                                device.generateMultiConnectionEvents(events[-1],events)
                        
                        _active_associations.append(uid)
                        self.wifi_associations[fritzbox_ip][uid] = [ uid, mac, gid, vlan, target_mac, target_interface, connection_details ]

                        _active_client_macs.append(mac)
                        self.wifi_clients[fritzbox_ip][mac] = True
                        
        for [ uid, mac, gid, vlan, target_mac, target_interface, connection_details ] in list(self.wifi_associations[fritzbox_ip].values()):
            if uid not in _active_associations:
                device = self.cache.getUnlockedDevice(mac)
                if device is not None:
                    device.lock(self)
                    device.removeHopConnection(Connection.WIFI, target_mac, target_interface, connection_details, True)
                    self.cache.confirmDevice( self, device )

                self.cache.removeConnectionStatDetails(self, target_mac,target_interface,connection_details)
                
                del self.wifi_associations[fritzbox_ip][uid]
                
                if mac not in _active_client_macs and mac in self.wifi_clients[fritzbox_ip]:
                    del self.wifi_clients[fritzbox_ip][mac]

#                        device = self.cache.getUnlockedDevice(mac)
#                        if device is not None:
#                            device.lock(self)
#                            device.addHopConnection(Connection.WIFI, target_mac, target_interface, connection_details );
#                            self.cache.confirmDevice( self, device )

#                            _active_client_macs.append(mac)
#                            self.wifi_clients[fritzbox_ip][mac] = True
                        
#                            stat = self.cache.getConnectionStat(target_mac,target_interface)
#                            stat_data = stat.getData(connection_details)
#                            stat_data.setInSpeed(node_link["cur_data_rate_rx"] * 1000)
#                            stat_data.setOutSpeed(node_link["cur_data_rate_tx"] * 1000)
#                            stat_data.setDetail("signal", node_link["rx_rcpi"], "attenuation")
#                            #stat_data.setDetail("signal", node_link["rx_rcpi"] if node_link["rx_rcpi"] != "255" else node_link["tx_rcpi"], "attenuation")
#                            self.cache.confirmStat( self, stat )

#                        _active_associations.append(uid)
#                        self.wifi_associations[fritzbox_ip][uid] = [ uid, mac, gid, vlan, target_mac, target_interface, connection_details ]
              
#        for [ uid, mac, gid, vlan, target_mac, target_interface, connection_details ] in list(self.wifi_associations[fritzbox_ip].values()):
#            if uid not in _active_associations:
#                device = self.cache.getUnlockedDevice(mac)
#                if device is not None:
#                    device.lock(self)
#                    device.removeHopConnection(Connection.WIFI, target_mac, target_interface, connection_details, True)
#                    self.cache.confirmDevice( self, device )
                    
#                    self.cache.removeConnectionStatDetails(self, target_mac,target_interface,connection_details)

#                del self.wifi_associations[fritzbox_ip][uid]
                
#                if mac not in _active_client_macs and mac in self.wifi_clients[fritzbox_ip]:
#                    del self.wifi_clients[fritzbox_ip][mac]
            
        self.cache.unlock(self)
                
    def _fetchDHCPClients(self, fritzbox_ip):
        self.next_run[fritzbox_ip]["dhcp_clients"] = datetime.now() + timedelta(seconds=self.config.fritzbox_client_interval)

        first_run = not self.known_clients[fritzbox_ip]

        # collect devices which are not processed or which are outdated
        new_clients = {}
        outdated_clients = {}
        reload_clients = {}
        if not first_run:
            devices = self.cache.getDevices()
            now = datetime.now()
            for device in devices:
                mac = device.getMAC()
                if mac is not None:
                    if mac not in self.dhcp_clients[fritzbox_ip]:
                        new_clients[mac] = device
                    elif (now - self.dhcp_clients[fritzbox_ip][mac]).total_seconds() >= self.config.fritzbox_network_interval:
                        outdated_clients[mac] = device
                else:
                    continue
                
            reload_clients = outdated_clients.copy()
            for mac in new_clients:
                if mac not in self.known_clients[fritzbox_ip]:
                    reload_clients[mac] = new_clients[mac]
                    
        if first_run or reload_clients:
            # check mac is not in known_clients or if known_clients is outdated
            
            start = datetime.now()

            # fetch full list
            if first_run or len(reload_clients.keys()) > 5:
                _hosts = {}
                for _host in self.fh[fritzbox_ip].get_generic_host_entries():
                    mac = _host["NewMACAddress"].lower()
                    _hosts[mac] = _host
                self.known_clients[fritzbox_ip] = _hosts
                Helper.logProfiler(self, start, "Full refresh of '{}'".format(fritzbox_ip))
            # for small amount of hosts, fetch individual data
            else:
                for mac in reload_clients:
                    try:
                        self.known_clients[fritzbox_ip][mac] = self.fh[fritzbox_ip].get_specific_host_entry(mac.upper())
                    except FritzLookUpError:
                        pass
                Helper.logProfiler(self, start, "Partial refresh of '{}'".format(fritzbox_ip))
                
            if first_run:
                _hosts = self.known_clients[fritzbox_ip]
                self.fritzbox_macs[fritzbox_ip] = next(mac for mac in _hosts.keys() if _hosts[mac]["NewIPAddress"] == fritzbox_ip )
                logging.info("Found {} for fritzbox {}".format(self.fritzbox_macs[fritzbox_ip], fritzbox_ip))
    
                devices = self.cache.getDevices()
                new_clients = {}
                for device in devices:
                    new_clients[device.getMAC()] = device
           
        obsolete_clients = []
        for device in devices:
            mac = device.getMAC()
            if mac not in self.known_clients[fritzbox_ip] and mac in self.dhcp_clients[fritzbox_ip]:
                obsolete_clients.append(device)

        if new_clients or outdated_clients or obsolete_clients:
            now = datetime.now()
            
            self.cache.lock(self)
            for device in (new_clients | outdated_clients).values():
                mac = device.getMAC()
                if mac in self.known_clients[fritzbox_ip]:
                    host = self.known_clients[fritzbox_ip][mac]
                    device.lock(self)
                    device.setIP("fritzbox-dhcp", 100, host["NewIPAddress"])
                    device.setDNS("fritzbox-dhcp", 100, host["NewHostName"])
                    self.dhcp_clients[fritzbox_ip][mac] = now
                    self.cache.confirmDevice( self, device )

            for device in obsolete_clients:
                mac = device.getMAC()
                device.lock(self)
                device.removeIP("fritzbox-dhcp")
                device.removeDNS("fritzbox-dhcp")
                del self.dhcp_clients[fritzbox_ip][device.getMAC()]
                self.cache.confirmDevice( self, device )
            self.cache.unlock(self)
                           
    def _fetchDeviceInfo(self, fritzbox_ip):
        self.next_run[fritzbox_ip]["device"] = datetime.now() + timedelta(seconds=self.config.fritzbox_client_interval)

        fritzbox_mac = self.fritzbox_macs[fritzbox_ip]
        
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

        self.cache.lock(self)

        now = datetime.now()
        
        fritzbox_device = self.cache.getUnlockedDevice(fritzbox_mac)
        if fritzbox_device is None or not fritzbox_device.hasIP("fritzbox"):
            fritzbox_device = self.cache.getDevice(fritzbox_mac)
            fritzbox_device.setIP("fritzbox", 100, fritzbox_ip)
            if fritzbox_mac == self.cache.getGatewayMAC():
                fritzbox_device.addHopConnection(Connection.ETHERNET, self.cache.getWanMAC(), self.cache.getWanInterface() );
            self.cache.confirmDevice( self, fritzbox_device )
        
        stat = self.cache.getConnectionStat(fritzbox_mac, self.cache.getGatewayInterface(self.config.default_vlan) )
        stat_data = stat.getData() 
        if fritzbox_ip in self.devices:
            time_diff = (now - self.devices[fritzbox_ip]).total_seconds()

            in_bytes = stat_data.getInBytes()
            if in_bytes is not None:
                byte_diff = lan_traffic_received - in_bytes
                if byte_diff > 0:
                    stat_data.setInAvg(byte_diff / time_diff)
                
            out_bytes = stat_data.getOutBytes()
            if out_bytes is not None:
                byte_diff = lan_traffic_sent - out_bytes
                if byte_diff > 0:
                    stat_data.setOutAvg(byte_diff / time_diff)
    
        stat_data.setInBytes(lan_traffic_received)
        stat_data.setOutBytes(lan_traffic_sent)
        #stat_data.setInSpeed(lan_link_state['down'] * 1000)
        stat_data.setInSpeed(1000000000)
        #stat_data.setOutSpeed(lan_link_state['up'] * 1000)
        stat_data.setOutSpeed(1000000000)
        #stat_data.setDetail("duplex", "full" if _port["duplex"] == "fullDuplex" else "half", "string")
        #stat_data.setDetail("duplex", lan_link_state["duplex"], "string")
        self.cache.confirmStat( self, stat )

        if fritzbox_mac == self.cache.getGatewayMAC():
            stat = self.cache.getConnectionStat(self.cache.getWanMAC(), self.cache.getWanInterface() )
            stat_data = stat.getData()
            stat_data.setDetail("wan_type",wan_link_state["type"], "string")
            stat_data.setDetail("wan_state",wan_link_state["state"], "string")

            if fritzbox_ip in self.devices:
                time_diff = (now - self.devices[fritzbox_ip]).total_seconds()

                in_bytes = stat_data.getInBytes()
                if in_bytes is not None:
                    byte_diff = wan_traffic_state["received"] - in_bytes
                    if byte_diff > 0:
                        stat_data.setInAvg(byte_diff / time_diff)
                    
                out_bytes = stat_data.getOutBytes()
                if out_bytes is not None:
                    byte_diff = wan_traffic_state["sent"] - out_bytes
                    if byte_diff > 0:
                        stat_data.setOutAvg(byte_diff / time_diff)
        
            stat_data.setInBytes(wan_traffic_state["received"])
            stat_data.setOutBytes(wan_traffic_state["sent"])
            stat_data.setInSpeed(wan_link_state["down"] * 1000)
            stat_data.setOutSpeed(wan_link_state["up"] * 1000)
            self.cache.confirmStat( self, stat )
                
        self.cache.unlock(self)
        
        self.devices[fritzbox_ip] = now

    def _isKnownDHCPClient(self, mac):
        for fritzbox_ip in self.fritzbox_devices:
            if mac in self.dhcp_clients[fritzbox_ip]:
                return True
        return False

    def _isKnownWifiClient(self, mac):
        for fritzbox_ip in self.fritzbox_devices:
            if mac in self.wifi_clients[fritzbox_ip]:
                return True
        return False
    
    def _delayedWakeup(self):
        with self.delayed_lock:
            self.delayed_wakeup_timer = None
            
            missing_dhcp_macs = []
            for mac in list(self.delayed_dhcp_devices.keys()):
                if not self._isKnownDHCPClient(mac):
                    missing_dhcp_macs.append(mac)
                del self.delayed_dhcp_devices[mac]

            missing_wifi_macs = []
            for mac in list(self.delayed_wifi_devices.keys()):
                if not self._isKnownWifiClient(mac):
                    missing_wifi_macs.append(mac)
                del self.delayed_wifi_devices[mac]
            
            triggered_types = {}
            for fritzbox_ip in self.next_run:
                if len(missing_dhcp_macs) > 0:
                    self.next_run[fritzbox_ip]["dhcp_clients"] = datetime.now()
                    triggered_types["dhcp"] = True
                if len(missing_wifi_macs) > 0:
                    self.next_run[fritzbox_ip]["mesh_clients"] = datetime.now()
                    triggered_types["wifi"] = True
                    
            if triggered_types:
                logging.info("Delayed trigger runs for {}".format(" & ".join(triggered_types)))

                self._wakeup()
            else:
                logging.info("Delayed trigger not needed anymore")

    def getEventTypes(self):
        return [ 
            { "types": [Event.TYPE_DEVICE], "actions": [Event.ACTION_CREATE], "details": None },
            { "types": [Event.TYPE_DEVICE_STAT], "actions": [Event.ACTION_MODIFY], "details": ["online_state"] }
        ]

    def processEvents(self, events):
        with self.delayed_lock:
            has_new_devices = False
            for event in events:
                if event.getType() == Event.TYPE_DEVICE_STAT:
                    stat = event.getObject()
                    device = self.cache.getUnlockedDevice(stat.getMAC())
                    if device is None:
                        logging.error("Unknown device for stat {}".format(stat))
                    
                    if not self.has_wifi_networks or not device.supportsWifi() or not stat.isOnline():
                        continue

                    self.delayed_wifi_devices[device.getMAC()] = device
                else:
                    device = event.getObject()
                    self.delayed_dhcp_devices[device.getMAC()] = device

                has_new_devices = True
                
                logging.info("Delayed trigger started for {}".format(device))

            if has_new_devices:
                if self.delayed_wakeup_timer is not None:
                    self.delayed_wakeup_timer.cancel()

                # delayed triggers try to group several event bulks into one
                self.delayed_wakeup_timer = threading.Timer(5,self._delayedWakeup)
                self.delayed_wakeup_timer.start()
