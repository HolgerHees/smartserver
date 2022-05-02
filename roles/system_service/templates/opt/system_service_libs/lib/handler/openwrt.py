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
        
        self.next_run = {}
        self.last_run = 0
        
        self.has_wifi_networks = False
        self.wifi_networks = {}
        
        self.wifi_associations = {}
        self.wifi_clients = {}
        
        self.condition = threading.Condition()
        self.thread = threading.Thread(target=self._checkOpenWRT, args=())

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
            
    def _checkOpenWRT(self):
        was_suspended = {}
                
        now = datetime.now().timestamp()

        for openwrt_ip in self.config.openwrt_devices:
            self.sessions[openwrt_ip] = [ None, datetime.now().timestamp()]

            self.next_run[openwrt_ip] = {"wifi_networks": now, "wifi_clients": now}
        
            self.wifi_networks[openwrt_ip] = {}

            self.wifi_associations[openwrt_ip] = {}
            self.wifi_clients[openwrt_ip] = {}
            
            was_suspended[openwrt_ip] = False
            
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
                    if was_suspended[openwrt_ip]:
                        logging.warning("Resume OpenWRT '{}'.".format(openwrt_ip))
                        was_suspended[openwrt_ip] = False
                        
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
                    logging.warning("{}. Will retry in {} seconds.".format(str(e), e.getTimeout()))
                    if timeout > e.getTimeout():
                        timeout = e.getTimeout()
                    was_suspended[openwrt_ip] = True
                except Exception as e:
                    self.cache.cleanLocks(self, events)

                    logging.error("OpenWRT '{}' got unexpected exception. Will suspend for 15 minutes.".format(openwrt_ip))
                    logging.error(traceback.format_exc())
                    if timeout > self.config.remote_error_timeout:
                        timeout = self.config.remote_error_timeout
                    was_suspended[openwrt_ip] = True
                    
            if len(events) > 0:
                self._getDispatcher().dispatch(self,events)

            if timeout > 0:
                with self.condition:
                    self.condition.wait(timeout)
                    
    def _processDevice(self, openwrt_ip, now, events, timeout ):
        openwrt_mac = self.cache.ip2mac(openwrt_ip)
        if openwrt_mac is None:
            raise NetworkException("OpenWRT '{}' not resolvable".format(openwrt_ip), 15)

        if now >= self.sessions[openwrt_ip][1]:
            result = self._getSession( openwrt_ip, self.config.openwrt_username, self.config.openwrt_password )
            self.sessions[openwrt_ip] = [ result["ubus_rpc_session"], now + result["expires"] - 10 ];

        if self.sessions[openwrt_ip][0] is None:
            return self.sessions[openwrt_ip][1] - now
        
        ubus_session_id = self.sessions[openwrt_ip][0]
                            
        if self.next_run[openwrt_ip]["wifi_networks"] <= now:
            [timeout, self.next_run[openwrt_ip]["wifi_networks"] ] = self._processWifiNetworks(openwrt_ip, ubus_session_id, now, events, timeout, self.config.openwrt_network_interval, openwrt_mac)
                            
        if self.next_run[openwrt_ip]["wifi_clients"] <= now:  
            [timeout, self.next_run[openwrt_ip]["wifi_clients"] ] = self._processWifiClients(openwrt_ip, ubus_session_id, now, events, timeout, self.config.openwrt_client_interval, openwrt_mac)
            
        return timeout
                
    def _processWifiNetworks(self, openwrt_ip, ubus_session_id, now, events, global_timeout, call_timeout, openwrt_mac):
        wifi_network_result = self._getWifiNetworks(openwrt_ip, ubus_session_id)
        
        wifi_network_changed = False
        
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
                ifname = _interface["ifname"];
                ssid = _interface["config"]["ssid"];
                band = _wifi_network["config"]["band"];
                gid = "{}-{}-{}".format(openwrt_ip,ssid,band)
                
                wifi_interface_details_result = self._getWifiInterfaceDetails(openwrt_ip, ubus_session_id, ifname)
                channel = wifi_interface_details_result["channel"]

                network = { 
                    "gid": gid,
                    "ifname": ifname,
                    "ssid": ssid,
                    "band": band,
                    "channel": channel,
                    "vlan": _active_vlans[ifname] if ifname in _active_vlans else self.config.default_vlan,
                    "device": wifi_network_name
                }
                
                if gid not in self.wifi_networks[openwrt_ip]:
                    wifi_network_changed = True
                
                _active_networks[gid] = network
                self.wifi_networks[openwrt_ip][gid] = network
                
        #print(self.wifi_networks[openwrt_ip])
        
        if _active_networks or self.wifi_networks[openwrt_ip]:
            self.cache.lock(self)

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
                    wifi_network_changed = True
                    
                    self.cache.removeGroup(gid, lambda event: events.append(event))
                    del self.wifi_networks[openwrt_ip][gid]
                    
            self.cache.unlock(self)
            
        if wifi_network_changed:
            # force a client refresh
            self.next_run[openwrt_ip]["wifi_clients"] = now
            
        # set device type
        device = self.cache.getUnlockedDevice(openwrt_mac)
        if device is not None and not device.hasType("openwrt"):
            self.cache.lock(self)
            device.lock(self)
            device.setType("openwrt", 100, "network")
            self.cache.confirmDevice( device, lambda event: events.append(event) )
            self.cache.unlock(self)
            
        has_wifi_networks = False
        for _openwrt_ip in self.config.openwrt_devices:
            if self.wifi_networks[_openwrt_ip]:
                has_wifi_networks = True
                break
        self.has_wifi_networks = has_wifi_networks

        if global_timeout > call_timeout:
            global_timeout = call_timeout

        return [global_timeout, now + call_timeout]
        
    def _processWifiClients(self, openwrt_ip, ubus_session_id, now, events, global_timeout, call_timeout, openwrt_mac):
        client_results = []
        for wlan_network in list(self.wifi_networks[openwrt_ip].values()):
            try:
                client_result = self._getWifiClients(openwrt_ip, ubus_session_id, wlan_network["ifname"])
            except UbusCallException as e:
                if e.getCode() == -32000:
                    logging.warning("OpenWRT '{}' interface '{}' has gone".format(openwrt_ip, wlan_network["ifname"]))
                    
                    # force refresh for wifi networks & clients
                    self.next_run[openwrt_ip]["wifi_networks"] = now
                    return [global_timeout, now]
                else:
                    raise e
            client_results.append([client_result,wlan_network])
                
        if client_results or self.wifi_associations[openwrt_ip]:
            self.cache.lock(self)

            _active_client_macs = []
            _active_client_wifi_associations = []
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
                    device.cleanDisabledHobConnections(target_mac, lambda event: events.append(event))
                    device.addHopConnection(Connection.WIFI, vlan, target_mac, target_interface);
                    device.addGID(gid)
                    self.cache.confirmDevice( device, lambda event: events.append(event) )

                    details = client_result["clients"][mac]
                   
                    stat = self.cache.getConnectionStat(target_mac,target_interface)
                    if not details["assoc"]: 
                        stat.setInAvg(0)
                        stat.setOutAvg(0)
                        stat.setInBytes(0)
                        stat.setOutBytes(0)
                        stat.setInSpeed(0)
                        stat.setOutSpeed(0)
                        stat.removeDetail("signal")
                    else:
                        if uid in self.wifi_associations[openwrt_ip]:
                            in_bytes = stat.getInBytes()
                            if in_bytes is not None:
                                time_diff = now - self.wifi_associations[openwrt_ip][uid][0]
                                byte_diff = details["bytes"]["rx"] - in_bytes
                                if byte_diff > 0:
                                    stat.setInAvg(byte_diff / time_diff)
                                
                            out_bytes = stat.getOutBytes()
                            if out_bytes is not None:
                                time_diff = now - self.wifi_associations[openwrt_ip][uid][0]
                                byte_diff = details["bytes"]["tx"] - out_bytes
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
                    _active_client_wifi_associations.append(uid)
                    self.wifi_associations[openwrt_ip][uid] = [ now, uid, mac, gid, vlan, target_mac, target_interface ]
                    
            wifi_clients = {}
            for [ _, uid, mac, gid, vlan, target_mac, target_interface ] in list(self.wifi_associations[openwrt_ip].values()):
                if uid not in _active_client_wifi_associations:
                    device = self.cache.getDevice(mac)
                    device.removeGID(gid);
                    # **** connection cleanup and stats cleanup happens in cleanDisabledHobConnection ****
                    device.disableHopConnection(Connection.WIFI, target_mac, target_interface)
                    self.cache.confirmDevice( device, lambda event: events.append(event) )
                    
                    del self.wifi_associations[openwrt_ip][uid]
                else:
                    wifi_clients[mac] = now
            self.wifi_clients[openwrt_ip] = wifi_clients
                    
            self.cache.unlock(self)
                    
        if global_timeout > call_timeout:
            global_timeout = call_timeout

        return [global_timeout, now + call_timeout]

    def _parseResult(self, ip, r, type):
        if r.status_code != 200:
            raise NetworkException("OpenWRT {} returns wrong status code: {}".format(openwrt_ip, r.status_code), self.config.remote_suspend_timeout)

        _json = r.text
        result = json.loads(_json)
        if "error" in result:
            raise UbusCallException( ip, type, result["error"]["code"], result["error"]["message"] )
        
        if "result" not in result or result["result"][0] != 0:
            raise UbusResponseException( ip, type, _json )

        return result["result"][1]
        #logging.warning("OpenWRT {} - {} - got unexpected device result '{}'".format(ip, type, _json))
        #return None
    
    def _post(self, ip, json):
        try:
            return requests.post( "https://{}/ubus".format(ip), json=json, verify=False)
        except requests.exceptions.ConnectionError as e:
            logging.error(str(e))
            raise NetworkException("OpenWRT {} currently not available".format(ip), self.config.remote_suspend_timeout)
        
    def _getSession(self, ip, username, password ):
        json = { "jsonrpc": "2.0", "id": 1, "method": "call", "params": [ "00000000000000000000000000000000", "session", "login", { "username": username, "password": password } ] }
        r = self._post(ip, json)
        return self._parseResult(ip, r, "session")
    
    def _getDevices(self, ip, session ):
        json = { "jsonrpc": "2.0", "id": 1, "method": "call", "params": [ session, "network.device", "status", {} ] }
        r = self._post(ip, json)
        return self._parseResult(ip, r, "device_list")

    def _getWifiNetworks(self, ip, session ):
        json = { "jsonrpc": "2.0", "id": 1, "method": "call", "params": [ session, "network.wireless", "status", {} ] }
        r = self._post(ip, json)
        return self._parseResult(ip, r, "device_list")

    def _getWifiInterfaceDetails(self, ip, session, interface ):
        json = { "jsonrpc": "2.0", "id": 1, "method": "call", "params": [ session, "hostapd.{}".format(interface), "get_status", {} ] }
        r = self._post(ip, json)
        return self._parseResult(ip, r, "device_details")

    def _getWifiClients(self, ip, session, interface ):
        json = { "jsonrpc": "2.0", "id": 1, "method": "call", "params": [ session, "hostapd.{}".format(interface), "get_clients", {} ] }
        r = self._post(ip, json)
        return self._parseResult(ip, r, "client_list")
        
    def _delayedWakeup(self):
        with self.delayed_lock:
            self.delayed_wakeup_timer = None
            
            missing_wifi_macs = []
            for mac in list(self.delayed_devices.keys()):
                for openwrt_ip in self.config.openwrt_devices:
                    if mac not in self.wifi_clients[openwrt_ip]:
                        missing_wifi_macs.append(mac)
                del self.delayed_devices[mac]
            
            triggered_types = {}
            for openwrt_ip in self.next_run:
                if len(missing_wifi_macs) > 0:
                    self.next_run[openwrt_ip]["wifi_clients"] = datetime.now().timestamp()
                    triggered_types["wifi"] = True
                    
            if triggered_types:
                logging.info("Delayed trigger runs for {}".format(" & ".join(triggered_types)))

                with self.condition:
                    self.condition.notifyAll()
            else:
                logging.info("Delayed trigger not needed anymore")
                
    def getEventTypes(self):
        return [ { "types": [Event.TYPE_STAT], "actions": [Event.ACTION_MODIFY], "details": ["online_state"] } ]

    def processEvents(self, events):
        with self.delayed_lock:
            has_new_devices = False
            for event in events:
                stat = event.getObject()
                device = self.cache.getUnlockedDevice(stat.getMAC())
                if device is None:
                    logging.error("Unknown device for stat {}".format(stat))
                
                if not self.has_wifi_networks or not device.supportsWifi():
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

class NetworkException(Exception):
    def __init__(self, msg, timeout):
        super().__init__(msg)
        
        self.timeout = timeout
        
    def getTimeout(self):
        return self.timeout

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
