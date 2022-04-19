import threading
from datetime import datetime, timedelta
import re
import requests
from urllib3.exceptions import InsecureRequestWarning
import json
import traceback

from smartserver import command

from lib.watcher import watcher
from lib.dto.device import Device
from lib.dto.group import Group
from lib.dto.stats import Stats
from lib.dto.event import Event
from lib.helper import Helper


class OpenWRT(watcher.Watcher): 
    def __init__(self, logger, config, handler ):
        super().__init__(logger)
      
        self.logger = logger
        self.config = config
        self.handler = handler
        
        self.is_running = True
        
        self.sessions = {}
        
        self.last_check = {}
        self.openwrt_macs = {}
        
        self.ap_wlan_networks = {}
        self.ap_wlan_clients = {}
        self.ap_client_connection_stats = {}
        
        self.condition = threading.Condition()
        self.thread = threading.Thread(target=self.checkOpenWRT, args=())
        
        self.data_lock = threading.Lock()
        
        requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

    def start(self):
        self.thread.start()
        
    def terminate(self):
        with self.condition:
            self.is_running = False
            self.condition.notifyAll()
            
    def checkOpenWRT(self):
        
        for openwrt_ip in self.config.openwrt_devices:
            self.last_check[openwrt_ip] = {"network": 0, "device": 0}
            self.openwrt_macs[openwrt_ip] = Helper.ip2mac(openwrt_ip)
        
        while self.is_running:
            now = datetime.now().timestamp()
            #RequestHeader set "X-Auth-Token" "{{vault_librenms_api_token}}"
            
            changes = {}

            timeout = 100000000
            
            for openwrt_ip in self.config.openwrt_devices:
                try:
                    timeout = self._processDevice(openwrt_ip, now, changes, timeout)
                except requests.exceptions.ConnectionError:
                    self.logger.warning("OpenWRT '{}' currently not available. Will suspend for 5 minutes.".format(openwrt_ip))
                    self.sessions[openwrt_ip] = [ None, now + self.config.openwrt_suspend_timeout ]
                    if timeout > self.config.openwrt_suspend_timeout:
                        timeout = self.config.openwrt_suspend_timeout
                except Exception as e:
                    self.logger.error("OpenWRT '{}' got unexpected exception. Will suspend for 15 minutes.".format(openwrt_ip))
                    self.logger.error(traceback.format_exc())
                    if timeout > self.config.openwrt_error_timeout:
                        timeout = self.config.openwrt_error_timeout
                    
            events = self._prepareEvents(changes)
            if len(events) > 0:
                self.handler.notify(self,events)

            if timeout > 0:
                with self.condition:
                    self.condition.wait(timeout)
                    
    def _processDevice(self, openwrt_ip, now, changes, timeout ):
        if openwrt_ip not in self.sessions or now >= self.sessions[openwrt_ip][1]:
            result = self._getSession( openwrt_ip, self.config.openwrt_username, self.config.openwrt_password )
            self.sessions[openwrt_ip] = [ result["ubus_rpc_session"], now + result["expires"] - 10 ];

        if self.sessions[openwrt_ip][0] is None:
            return self.sessions[openwrt_ip][0][1] - now
        
        ubus_session_id = self.sessions[openwrt_ip][0]
                            
        if now - self.last_check[openwrt_ip]["network"] >= self.config.openwrt_network_interval:
            [timeout, self.last_check[openwrt_ip]["network"] ] = self._getWifiNetworks(openwrt_ip, ubus_session_id, now, changes, timeout, self.config.openwrt_network_interval)
                            
        if now - self.last_check[openwrt_ip]["device"] >= self.config.openwrt_device_interval:
            self.last_check[openwrt_ip]["device"] = now
            if timeout > self.config.openwrt_device_interval:
                timeout = self.config.openwrt_device_interval
                
            _active_client_macs = []
            for wlan_network in list(self.ap_wlan_networks[openwrt_ip].values()):
                try:
                    client_result = self._getClients(openwrt_ip, ubus_session_id, wlan_network["ifname"])
                except UbusCallException as e:
                    if e.getCode() == -32000:
                        self.logger.warning("OpenWRT '{}' interface '{}' has gone".format(openwrt_ip, wlan_network["ifname"]))
                        self.last_check[openwrt_ip]["network"] = 0 # => force refresh next time
                        continue
                    else:
                        raise e

                with self.data_lock:
                    for mac in client_result["clients"]:
                        client = {
                            "mac": mac
                        }
                        _active_client_macs.append(mac)

                        if openwrt_ip not in self.ap_wlan_clients:
                            self.ap_wlan_clients[openwrt_ip] = {}
                            
                        if mac not in self.ap_wlan_clients[openwrt_ip] or not self.data_equal(self.ap_wlan_clients[openwrt_ip][mac], client):
                            self._appendChange(changes, Event.TYPE_DEVICE, mac, {"action": "change", "openwrt_ip": openwrt_ip, "network": wlan_network})
                            self.ap_wlan_clients[openwrt_ip][mac] = client
                        
                        details = client_result["clients"][mac]
                        if not details["assoc"]: 
                            continue
                        
                        in_avg = 0
                        out_avg = 0
                        if openwrt_ip in self.ap_client_connection_stats and mac in self.ap_client_connection_stats[openwrt_ip]:
                            _client_connection_stats = self.ap_client_connection_stats[openwrt_ip][mac]
                            time_diff = (now - _client_connection_stats["last_check"])

                            in_diff = details["bytes"]["rx"] - _client_connection_stats["in_traffic"]
                            if in_diff < 0: # => counter overflow
                                in_avg = _client_connection_stats["in_avg"]
                            else:
                                in_avg = in_diff / time_diff

                            out_diff = details["bytes"]["tx"] - _client_connection_stats["out_traffic"]
                            if out_diff < 0: # => counter overflow
                                out_avg = _client_connection_stats["out_avg"]
                            else:
                                out_avg = in_diff / time_diff

                        stat = {
                            "mac": mac,
                            "in_traffic": details["bytes"]["rx"],
                            "in_avg": in_avg,
                            "out_traffic": details["bytes"]["tx"],
                            "out_avg": out_avg,
                            "in_speed": details["rate"]["rx"] * 1000,
                            "out_speed": details["rate"]["tx"] * 1000,
                            "signal": details["signal"],
                            "last_check": now
                        }
                        
                        if openwrt_ip not in self.ap_client_connection_stats:
                            self.ap_client_connection_stats[openwrt_ip] = {}
                            
                        if mac not in self.ap_client_connection_stats[openwrt_ip] or not self.data_equal(self.ap_client_connection_stats[openwrt_ip][mac], stat):
                            self._appendChange(changes, Event.TYPE_DEVICE_STAT, mac, {"action": "change", "openwrt_ip": openwrt_ip, "stat": stat})
                            self.ap_client_connection_stats[openwrt_ip][mac] = stat
                            
                with self.data_lock:
                    for mac in list(self.ap_wlan_clients[openwrt_ip]):
                        if mac not in _active_client_macs:
                            self.logger.info("Clean mac '{}'".format(mac))
                            self._appendChange(changes, Event.TYPE_DEVICE, mac, {"action": "delete", "openwrt_ip": openwrt_ip, "network": wlan_network } )
                            self._appendChange(changes, Event.TYPE_DEVICE_STAT, mac, {"action": "delete", "openwrt_ip": openwrt_ip, "stat": self.ap_client_connection_stats[openwrt_ip][mac]} )
                            del self.ap_wlan_clients[openwrt_ip][mac]
                            del self.ap_client_connection_stats[openwrt_ip][mac]
                    pass
                    
        return timeout
                
    def _getWifiNetworks(self, openwrt_ip, ubus_session_id, now, changes, global_timeout, call_timeout):
        devices_result = self._getDevices(openwrt_ip, ubus_session_id)
        with self.data_lock:
            _active_gids = []
            for device_name in devices_result:
                _device = devices_result[device_name]
                for _interface in _device["interfaces"]:
                    #print(_interface)
                    
                    gid = "{}-{}".format(openwrt_ip,_interface["ifname"])
                    _active_gids.append(gid)
                    
                    wlan_network = { 
                        "gid": gid,
                        "ifname": _interface["ifname"],
                        "ssid": _interface["config"]["ssid"],
                        "band": _device["config"]["band"],
                        "channel": None,
                        "vlan": _interface["vlan"][0] if len(_interface["vlans"]) > 0 else None,
                        "device": device_name
                    }

                    device_details_result = self._getDeviceDetails(openwrt_ip, ubus_session_id, _interface["ifname"])
                    wlan_network["channel"] = device_details_result["channel"]
                        
                    #print(wlan_network)
                    
                    if openwrt_ip not in self.ap_wlan_networks:
                        self.ap_wlan_networks[openwrt_ip] = {}
                
                    if gid not in self.ap_wlan_networks[openwrt_ip] or not self.data_equal(self.ap_wlan_networks[openwrt_ip][gid], wlan_network):
                        self._appendChange(changes, Event.TYPE_GROUP, gid, {"action": "change", "openwrt_ip": openwrt_ip, "wlan_network": wlan_network})
                        self.ap_wlan_networks[openwrt_ip][gid] = wlan_network
                        
            for gid in list(self.ap_wlan_networks[openwrt_ip]):
                if gid not in _active_gids:
                    self.logger.info("Clean gid '{}'".format(gid))
                    self._appendChange(changes, Event.TYPE_GROUP, gid, {"action": "delete", "openwrt_ip": openwrt_ip, "wlan_network": wlan_network})
                    del self.ap_wlan_networks[openwrt_ip][gid]
        
        if global_timeout > call_timeout:
            global_timeout = call_timeout

        return [global_timeout, now]
        
    def _parseResult(self, ip, _json, type):
        result = json.loads(_json)
        if "error" in result:
            raise UbusCallException( ip, type, result["error"]["code"], result["error"]["message"] )
        
        if "result" not in result or result["result"][0] != 0:
            raise UbusResponseException( ip, type, _json )

        return result["result"][1]

        self.logger.warning("OpenWRT {} - {} - got unexpected device result '{}'".format(ip, type, _json))
        return None
        
    def _getSession(self, ip, username, password ):
        json = { "jsonrpc": "2.0", "id": 1, "method": "call", "params": [ "00000000000000000000000000000000", "session", "login", { "username": username, "password": password } ] }
        r = requests.post( "https://{}/ubus".format(ip), json=json, verify=False)
        return self._parseResult(ip, r.text, "session")
    
    def _getDevices(self, ip, session ):
        json = { "jsonrpc": "2.0", "id": 1, "method": "call", "params": [ session, "network.wireless", "status", {} ] }
        r = requests.post( "https://{}/ubus".format(ip), json=json, verify=False)
        return self._parseResult(ip, r.text, "device_list")

    def _getDeviceDetails(self, ip, session, interface ):
        json = { "jsonrpc": "2.0", "id": 1, "method": "call", "params": [ session, "hostapd.{}".format(interface), "get_status", {} ] }
        r = requests.post( "https://{}/ubus".format(ip), json=json, verify=False)
        return self._parseResult(ip, r.text, "device_details")

    def _getClients(self, ip, session, interface ):
        json = { "jsonrpc": "2.0", "id": 1, "method": "call", "params": [ session, "hostapd.{}".format(interface), "get_clients", {} ] }
        r = requests.post( "https://{}/ubus".format(ip), json=json, verify=False)
        return self._parseResult(ip, r.text, "client_list")

    def triggerEvents(self, groups, devices, stats, events):
        for event in events:
            if event.getAction() != Event.ACTION_CREATE or event.getType() != Event.TYPE_DEVICE:
                continue
            
            #mac = event.getIdentifier()
            #device = list(filter(lambda d: d.getMAC() == mac, devices ))[0]
            
            #for openwrt_ip in self.ap_wlan_networks:
            #    if device.getIP() == openwrt_ip:
            #        for mac in self.ap_wlan_clients[openwrt_ip]:
            #            _source_devices = list(filter(lambda d: d.getMAC() == mac, devices ))
            #            self._fillConnection(openwrt_ip, _source_devices[0], device, self.ap_wlan_clients[openwrt_ip][mac], True)
            
            #known_macs = []
            #for ip in self.ap_wlan_clients:
            #    for mac in self.ap_wlan_clients[ip]:
            #        known_macs.append(mac)
                    
            #unknown_macs = []
            #mac = event.getIdentifier():
            #if mac not in known_macs:
            #    unknown_macs.append(mac)
                    
            #if len(unknown_macs) > 0:
            #    self.logger.info("Trigger refresh for unknown macs {}".format(unknown_macs))
            
            #    for openwrt_ip in self.config.openwrt_devices:
            #        self.last_check[openwrt_ip]["device"] = 0
            
            #    with self.condition:
            #        self.condition.notifyAll()
    
            #break

    def processEvents(self, groups, devices, stats, events):
        for event in events:
            if event.getType() == Event.TYPE_GROUP:
                gid = event.getIdentifier()
                action = event.getPayload("action")
                if action == "delete":
                    for group in list(filter(lambda g: g.getGID() == gid, groups)):
                        self.logger.info("Clean group {}".format(gid))
                        event.setAction(Event.ACTION_DELETE)

                        groups.remove(stat)
                else:
                    _groups = list(filter(lambda g: g.getGID() == gid, groups))
                    if len(_groups) > 0:
                        self.logger.info("Update group {}".format(gid))
                        event.setAction(Event.ACTION_MODIFY)

                        group = _groups[0]
                    else:
                        self.logger.info("Add group {}".format(gid))
                        event.setAction(Event.ACTION_CREATE)

                        group = Group(gid,"wlan")
                        groups.append(group)
                        
                    openwrt_ip = event.getPayload("openwrt_ip" )
                    _wlan_network = event.getPayload("wlan_network" )
                       
                    for key in _wlan_network:
                        if key in ["ifname","device","vlan"]:
                            continue
                        group.appendDetails(key, _wlan_network[key])
                        
            elif event.getType() == Event.TYPE_DEVICE:
                mac = event.getIdentifier()
                
                openwrt_ip = event.getPayload("openwrt_ip" )
                #_wlan_client = event.getPayload("client")
                _wlan_network = event.getPayload("network")

                if event.getPayload("action") == "delete":
                    for device in list(filter(lambda d: d.getMAC() == mac, devices )):
                        self.logger.info("Clean connection from {} to {}".format(device, device.getConnectionTargetUID()))
                        
                        if device.getConnectionTargetUID() == self.openwrt_macs[openwrt_ip] and device.getConnectionPort() == _wlan_network["ifname"]:
                            device.removeConnectionTarget(Device.CONNECTION_TYPE_WIFI);
                            device.removeGID(event.getPayload("gid"))
                        
                            event.setAction(Event.ACTION_MODIFY)
                else:
                    _devices = list(filter(lambda d: d.getMAC() == mac, devices ))
                    if len(_devices) > 0:
                        device = _devices[0]

                        self.logger.info("Update device {}".format(device))
                        event.setAction(Event.ACTION_MODIFY)
                    else:
                        device = Device(mac,"device")
                        device.setMAC(mac)
                        #device.setIp(_arp_device["ip"])
                        devices.append(device)

                        self.logger.info("Add device {}".format(device))
                        event.setAction(Event.ACTION_CREATE)
                        
                        self._fillConnection(openwrt_ip, device, devices, _wlan_network, False)
                        
            elif event.getType() == Event.TYPE_DEVICE_STAT:
                mac = event.getIdentifier()

                _devices = list(filter(lambda d: d.getMAC() == mac, devices ))
                device = _devices[0] if len(_devices) > 0 else None
                
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

                openwrt_ip = event.getPayload("openwrt_ip" )
                _stat = event.getPayload("stat" )

                stat.setInBytes(_stat["in_traffic"])
                stat.setInAvg(_stat["in_avg"])
                stat.setOutBytes(_stat["out_traffic"])
                stat.setOutAvg(_stat["out_avg"])
                stat.setInSpeed(_stat["in_speed"])
                stat.setOutSpeed(_stat["out_speed"])

                stat.appendDetails("signal", _stat["signal"])
                       

    def _fillConnection(self, openwrt_ip, source_device, devices, _wlan_network, is_lazy):
        _target_devices = list(filter(lambda d: d.getMAC() == self.openwrt_macs[openwrt_ip], devices ))
        _target = _target_devices[0] if len(_target_devices) > 0 else self.openwrt_macs[openwrt_ip]

        self.logger.info("Update{} connection from {} to {}".format(" lazy" if is_lazy else "", source_device, _target))
        
        source_device.setConnectionTarget(self.openwrt_macs[openwrt_ip], _wlan_network["ifname"], _wlan_network["vlan"], Device.CONNECTION_TYPE_WIFI );

        source_device.addGID(_wlan_network["gid"])

class UbusCallException(Exception):
    def __init__(self, ip, type, code, message):
        super().__init__(message)
            
        self.ip = ip
        self.type = type
        self.code = code
        
    def getCode(self):
        return self.code
    
class UbusResponseException(Exception):
    def __init__(self, ip, type, message):
        super().__init__(message)
            
        self.ip = ip
        self.type = type
