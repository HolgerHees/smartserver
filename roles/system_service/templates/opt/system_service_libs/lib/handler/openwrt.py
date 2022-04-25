import threading
from datetime import datetime, timedelta
import re
import requests
from urllib3.exceptions import InsecureRequestWarning
import json
import traceback
import logging

from smartserver import command

from lib.handler import _handler
from lib.dto._changeable import Changeable
from lib.dto.device import Device, Connection
from lib.dto.group import Group
from lib.dto.event import Event
from lib.helper import Helper


class OpenWRT(_handler.Handler): 
    def __init__(self, config, cache ):
        super().__init__()
      
        self.config = config
        self.cache = cache
        
        self.is_running = True
        
        self.sessions = {}
        
        self.last_check = {}
        self.last_run = 0
        
        self.client_wifi_connections = {}
        self.wifi_networks = {}
        
        self.condition = threading.Condition()
        self.thread = threading.Thread(target=self._checkOpenWRT, args=())

        self.delayed_wakeup_timer = None

        requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

    def start(self):
        self.thread.start()
        
    def terminate(self):
        with self.condition:
            self.is_running = False
            self.condition.notifyAll()
            
    def _checkOpenWRT(self):
        for openwrt_ip in self.config.openwrt_devices:
            self.sessions[openwrt_ip] = [ None, datetime.now().timestamp()]

            self.last_check[openwrt_ip] = {"network": 0, "client": 0}
        
            self.client_wifi_connections[openwrt_ip] = {}
            self.wifi_networks[openwrt_ip] = {}
            
        was_suspended = False
                
        while self.is_running:
            if self.delayed_wakeup_timer is not None:
                self.delayed_wakeup_timer.cancel()
                self.delayed_wakeup_timer = None
                    
            now = datetime.now().timestamp()
            #RequestHeader set "X-Auth-Token" "{{vault_librenms_api_token}}"
            
            self.last_run = now
            
            events = []

            timeout = 100000000
            
            for openwrt_ip in self.config.openwrt_devices:
                try:
                    if was_suspended:
                        logging.warning("Resume OpenWRT '{}'.".format(openwrt_ip))
                        was_suspended = False
                        
                    timeout = self._processDevice(openwrt_ip, now, events, timeout)
                except UbusCallException as e:
                    if self.sessions[openwrt_ip][0] is not None and e.getCode() == -32002:
                        logging.info("OpenWRT '{}' has invalid session. Will refresh.".format(openwrt_ip))
                        self.sessions[openwrt_ip] = [ None, now ]
                        timeout = 0
                    else:
                        logging.error("OpenWRT '{}' got exception {} - '{}'. Will suspend for 15 minutes.".format(openwrt_ip, e.getCode(), e))
                        timeout = self.config.remote_error_timeout
                except NetworkException as e:
                    logging.warning("{}. Will retry in 15 seconds.".format(e))
                    if timeout > 15:
                        timeout = 15
                except requests.exceptions.ConnectionError:
                    logging.warning("OpenWRT '{}' not available. Will suspend for 5 minutes.".format(openwrt_ip))
                    self.sessions[openwrt_ip] = [ None, now + self.config.remote_suspend_timeout ]
                    if timeout > self.config.remote_suspend_timeout:
                        timeout = self.config.remote_suspend_timeout
                    was_suspended = True
                except Exception as e:
                    logging.error("OpenWRT '{}' got unexpected exception. Will suspend for 15 minutes.".format(openwrt_ip))
                    logging.error(traceback.format_exc())
                    if timeout > self.config.remote_error_timeout:
                        timeout = self.config.remote_error_timeout
                    was_suspended = True
                    
            if len(events) > 0:
                self._getDispatcher().dispatch(self,events)

            if timeout > 0:
                with self.condition:
                    self.condition.wait(timeout)
                    
    def _processDevice(self, openwrt_ip, now, events, timeout ):
        openwrt_mac = self.cache.ip2mac(openwrt_ip)
        if openwrt_mac is None:
            raise NetworkException("OpenWRT '{}' not resolvable".format(openwrt_ip))

        if now >= self.sessions[openwrt_ip][1]:
            result = self._getSession( openwrt_ip, self.config.openwrt_username, self.config.openwrt_password )
            self.sessions[openwrt_ip] = [ result["ubus_rpc_session"], now + result["expires"] - 10 ];

        if self.sessions[openwrt_ip][0] is None:
            return self.sessions[openwrt_ip][1] - now
        
        ubus_session_id = self.sessions[openwrt_ip][0]
                            
        if now - self.last_check[openwrt_ip]["network"] >= self.config.openwrt_network_interval:
            [timeout, self.last_check[openwrt_ip]["network"] ] = self._processWifiNetworks(openwrt_ip, ubus_session_id, now, events, timeout, self.config.openwrt_network_interval)
                            
        if now - self.last_check[openwrt_ip]["client"] >= self.config.openwrt_client_interval:  
            [timeout, self.last_check[openwrt_ip]["client"] ] = self._processWifiClients(openwrt_ip, ubus_session_id, now, events, timeout, self.config.openwrt_client_interval, openwrt_mac)
            
        return timeout
                
    def _processWifiNetworks(self, openwrt_ip, ubus_session_id, now, events, global_timeout, call_timeout):
        wifi_network_result = self._getWifiNetworks(openwrt_ip, ubus_session_id)
        
        _active_vlans = {}
        device_result = self._getDevices(openwrt_ip, ubus_session_id)
        for device_name in device_result:
            _device = device_result[device_name]
            if "bridge-vlans" not in _device:
                continue
            for vlan in _device["bridge-vlans"]:
                for port in vlan["ports"]:
                    _active_vlans[port] = vlan["id"]
        
        _active_networks = {}
        for wifi_network_name in wifi_network_result:
            _wifi_network = wifi_network_result[wifi_network_name]
            for _interface in _wifi_network["interfaces"]:
                gid = "{}-{}".format(openwrt_ip,_interface["ifname"])
                
                wifi_interface_details_result = self._getWifiInterfaceDetails(openwrt_ip, ubus_session_id, _interface["ifname"])
                channel = wifi_interface_details_result["channel"]

                network = { 
                    "gid": gid,
                    "ifname": _interface["ifname"],
                    "ssid": _interface["config"]["ssid"],
                    "band": _wifi_network["config"]["band"],
                    "channel": channel,
                    "vlan": _active_vlans[_interface["ifname"]] if _interface["ifname"] in _active_vlans else self.config.default_vlan,
                    "device": wifi_network_name
                }
                
                _active_networks[gid] = network
                self.wifi_networks[openwrt_ip][gid] = network
                
        #print(self.wifi_networks[openwrt_ip])
        
        if _active_networks or self.wifi_networks[openwrt_ip]:
            self.cache.lock()

            for gid in _active_networks:
                network = _active_networks[gid]

                group = self.cache.getGroup(gid, Group.WIFI)
                group.setDetail("ssid", network["ssid"], "string")
                group.setDetail("band", network["band"], "string")
                group.setDetail("channel", network["channel"], "string")
                #group.setDetail("vlan", network["vlan"], "string")
                self.cache.confirmGroup(group, lambda event: events.append(event))
                        
            for gid in list(self.wifi_networks[openwrt_ip].keys()):
                if gid not in _active_networks:
                    self.cache.removeGroup(gid, lambda event: events.append(event))
                    del self.wifi_networks[openwrt_ip][gid]
                    
            self.cache.unlock()
        
        if global_timeout > call_timeout:
            global_timeout = call_timeout

        return [global_timeout, now]
        
    def _processWifiClients(self, openwrt_ip, ubus_session_id, now, events, global_timeout, call_timeout, openwrt_mac):
        client_results = []
        for wlan_network in list(self.wifi_networks[openwrt_ip].values()):
            try:
                client_result = self._getWifiClients(openwrt_ip, ubus_session_id, wlan_network["ifname"])
            except UbusCallException as e:
                if e.getCode() == -32000:
                    logging.warning("OpenWRT '{}' interface '{}' has gone".format(openwrt_ip, wlan_network["ifname"]))
                    self.last_check[openwrt_ip]["network"] = 0 # => force refresh next time
                    continue
                else:
                    raise e
            client_results.append([client_result,wlan_network])
                
        if client_results or self.client_wifi_connections[openwrt_ip]:
            self.cache.lock()

            _active_client_macs = []
            _active_client_wifi_connections = []
            for [client_result,wlan_network] in client_results:
                #logging.info(client_result)
                for mac in client_result["clients"]:
                    if mac == self.cache.getGatewayMAC():
                        continue
                
                    target_mac = openwrt_mac
                    target_interface = mac#wlan_network["ssid"]
                    vlan = wlan_network["vlan"]
                    gid = wlan_network["gid"]
                    
                    uid = "{}-{}".format(mac, gid)

                    device = self.cache.getDevice(mac)
                    device.addHopConnection(Connection.WIFI, vlan, target_mac, target_interface);
                    device.addGID(gid)
                    self.cache.confirmDevice( device, lambda event: events.append(event) )

                    details = client_result["clients"][mac]
                    if not details["assoc"]: 
                        continue
                    
                    stat = self.cache.getConnectionStat(target_mac,target_interface)
                    if uid in self.client_wifi_connections[openwrt_ip]:
                        in_bytes = stat.getInBytes()
                        if in_bytes > 0:
                            time_diff = now - self.client_wifi_connections[openwrt_ip][uid][0]
                            byte_diff = details["bytes"]["rx"] - in_bytes
                            if byte_diff > 0:
                                stat.setInAvg(byte_diff / time_diff)
                            
                        outBytes = stat.getOutBytes()
                        if outBytes > 0:
                            time_diff = now - self.client_wifi_connections[openwrt_ip][uid][0]
                            byte_diff = details["bytes"]["tx"] - outBytes
                            if byte_diff > 0:
                                stat.setOutAvg(byte_diff / time_diff)

                    #stat.setOnline(True) # => will be set bei arpscan listener
                    stat.setInBytes(details["bytes"]["rx"])
                    stat.setOutBytes(details["bytes"]["tx"])
                    stat.setInSpeed(details["rate"]["rx"] * 1000)
                    stat.setOutSpeed(details["rate"]["tx"] * 1000)
                    stat.setDetail("signal", details["signal"], "attenuation")
                    
                    self.cache.confirmStat( stat, lambda event: events.append(event) )
                        
                    _active_client_macs.append(mac)
                    _active_client_wifi_connections.append(uid)
                    self.client_wifi_connections[openwrt_ip][uid] = [ now, uid, mac, gid, vlan, target_mac, target_interface ]
                    
            for [ _, uid, mac, gid, vlan, target_mac, target_interface ] in list(self.client_wifi_connections[openwrt_ip].values()):
                if uid not in _active_client_wifi_connections:
                    device = self.cache.getDevice(mac)
                    # connection should still exists, also when device becomes offline
                    #device.removeHopConnection(vlan, target_mac, target_interface)
                    device.removeGID(gid)
                    self.cache.confirmDevice( device, lambda event: events.append(event) )
                    
                    if mac not in _active_client_macs:
                        stat = self.cache.removeConnectionStat(target_mac, target_interface, lambda event: events.append(event))
                    
                    del self.client_wifi_connections[openwrt_ip][uid]
                        
            self.cache.unlock()
                    
        if global_timeout > call_timeout:
            global_timeout = call_timeout

        return [global_timeout, now]

    def _parseResult(self, ip, r, type):
        if r.status_code != 200:
            msg = "Wrong status code: {}".format(r.status_code)
            logging.error(msg)
            raise requests.exceptions.ConnectionError(msg)

        _json = r.text
        result = json.loads(_json)
        if "error" in result:
            raise UbusCallException( ip, type, result["error"]["code"], result["error"]["message"] )
        
        if "result" not in result or result["result"][0] != 0:
            raise UbusResponseException( ip, type, _json )

        return result["result"][1]
        #logging.warning("OpenWRT {} - {} - got unexpected device result '{}'".format(ip, type, _json))
        #return None
        
    def _getSession(self, ip, username, password ):
        json = { "jsonrpc": "2.0", "id": 1, "method": "call", "params": [ "00000000000000000000000000000000", "session", "login", { "username": username, "password": password } ] }
        r = requests.post( "https://{}/ubus".format(ip), json=json, verify=False)
        return self._parseResult(ip, r, "session")
    
    def _getDevices(self, ip, session ):
        json = { "jsonrpc": "2.0", "id": 1, "method": "call", "params": [ session, "network.device", "status", {} ] }
        r = requests.post( "https://{}/ubus".format(ip), json=json, verify=False)
        return self._parseResult(ip, r, "device_list")

    def _getWifiNetworks(self, ip, session ):
        json = { "jsonrpc": "2.0", "id": 1, "method": "call", "params": [ session, "network.wireless", "status", {} ] }
        r = requests.post( "https://{}/ubus".format(ip), json=json, verify=False)
        return self._parseResult(ip, r, "device_list")

    def _getWifiInterfaceDetails(self, ip, session, interface ):
        json = { "jsonrpc": "2.0", "id": 1, "method": "call", "params": [ session, "hostapd.{}".format(interface), "get_status", {} ] }
        r = requests.post( "https://{}/ubus".format(ip), json=json, verify=False)
        return self._parseResult(ip, r, "device_details")

    def _getWifiClients(self, ip, session, interface ):
        json = { "jsonrpc": "2.0", "id": 1, "method": "call", "params": [ session, "hostapd.{}".format(interface), "get_clients", {} ] }
        r = requests.post( "https://{}/ubus".format(ip), json=json, verify=False)
        return self._parseResult(ip, r, "client_list")
        
    def _delayedWakeup(self, triggered_at):
        self.delayed_wakeup_timer = None
        
        if self.last_run > triggered_at:
            logging.info("Delayed trigger not needed anymore")
            return
        
        for openwrt_ip in self.last_check:
            self.last_check[openwrt_ip]["client"] = datetime.now().timestamp() - self.config.openwrt_client_interval
        with self.condition:
            self.condition.notifyAll()

    def getEventTypes(self):
        return [ { "types": [Event.TYPE_DEVICE], "actions": [Event.ACTION_CREATE], "details": None } ]

    def processEvents(self, events):
        for event in events:
            device = event.getObject()
            if device.supportsWifi():
                if self.delayed_wakeup_timer is not None:
                    self.delayed_wakeup_timer.cancel()
                logging.info("Delayed trigger started for {}".format(device))
                self.delayed_wakeup_timer = threading.Timer(5,self._delayedWakeup,[datetime.now().timestamp()])
                self.delayed_wakeup_timer.start()

class NetworkException(Exception):
    pass

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
