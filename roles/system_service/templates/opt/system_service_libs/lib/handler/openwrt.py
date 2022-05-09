import threading
from datetime import datetime, timedelta
import re
import requests
from urllib3.exceptions import InsecureRequestWarning
import json
import traceback
import logging
#import cProfile, pstats
#from pstats import SortKey

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
        
        self.sessions = {}
        
        self.next_run = {}
        
        self.has_wifi_networks = False
        self.wifi_networks = {}
        
        self.wifi_associations = {}
        self.wifi_clients = {}
        
        self.delayed_lock = threading.Lock()
        self.delayed_devices = {}
        self.delayed_wakeup_timer = None

        requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

    def _run(self):
        now = datetime.now()

        for openwrt_ip in self.config.openwrt_devices:
            self.sessions[openwrt_ip] = [ None, datetime.now()]

            self.next_run[openwrt_ip] = {"wifi_networks": now, "wifi_clients": now}
        
            self.wifi_networks[openwrt_ip] = {}

            self.wifi_associations[openwrt_ip] = {}
            self.wifi_clients[openwrt_ip] = {}
            
        while self._isRunning():
            #RequestHeader set "X-Auth-Token" "{{vault_librenms_api_token}}"
            
            events = []

            timeout = 9999999999
            
            for openwrt_ip in self.config.openwrt_devices:
                try:
                    if self._isSuspended(openwrt_ip):
                        self._confirmSuspended(openwrt_ip)
                        
                    self._processDevice(openwrt_ip, events)
                except UbusCallException as e:
                    if self.sessions[openwrt_ip][0] is not None and e.getCode() == -32002:
                        logging.info("OpenWRT '{}' has invalid session. Will refresh.".format(openwrt_ip))
                        self.sessions[openwrt_ip] = [ None, datetime.now() ]
                        timeout = 0
                    else:
                        logging.error("OpenWRT '{}' got exception {} - '{}'. Will suspend for 15 minutes.".format(openwrt_ip, e.getCode(), e))
                        timeout = self.config.remote_error_timeout
                        self._suspend(openwrt_ip)
                except NetworkException as e:
                    logging.warning("{}. Will retry in {} seconds.".format(str(e), e.getTimeout()))
                    timeout = e.getTimeout()
                    self._suspend(openwrt_ip)
                except Exception as e:
                    self.cache.cleanLocks(self, events)
                    timeout = self._handleUnexpectedException(e, openwrt_ip)
                    
            if len(events) > 0:
                self._getDispatcher().dispatch(self,events)
                
            now = datetime.now()
            for openwrt_ip in self.config.openwrt_devices:
                for next_run in self.next_run[openwrt_ip].values():
                    diff = (next_run - now).total_seconds()
                    if diff < timeout:
                        timeout = diff

            if timeout > 0:
                if self._isSuspended(openwrt_ip):
                    self._sleep(timeout)
                else:
                    self._wait(timeout)
                    
    def _processDevice(self, openwrt_ip, events ):
        openwrt_mac = self.cache.ip2mac(openwrt_ip)
        if openwrt_mac is None:
            raise NetworkException("OpenWRT '{}' not resolvable".format(openwrt_ip), 15)

        if datetime.now() >= self.sessions[openwrt_ip][1]:
            result = self._getSession( openwrt_ip, self.config.openwrt_username, self.config.openwrt_password )
            self.sessions[openwrt_ip] = [ result["ubus_rpc_session"], datetime.now() + timedelta(seconds=result["expires"] - 10 ) ];

        if self.sessions[openwrt_ip][0] is None:
            return self.sessions[openwrt_ip][1] - now
        
        ubus_session_id = self.sessions[openwrt_ip][0]
                            
        if self.next_run[openwrt_ip]["wifi_networks"] <= datetime.now():
            self._processWifiNetworks(openwrt_ip, ubus_session_id, events, openwrt_mac)
                            
        if self.next_run[openwrt_ip]["wifi_clients"] <= datetime.now():  
            self._processWifiClients(openwrt_ip, ubus_session_id, events, openwrt_mac)
                
    def _processWifiNetworks(self, openwrt_ip, ubus_session_id, events, openwrt_mac):
        self.next_run[openwrt_ip]["wifi_networks"] = datetime.now() + timedelta(seconds=self.config.openwrt_network_interval)

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
                priority = 1 if channel > 13 else 0
                
                network = { 
                    "gid": gid,
                    "ifname": ifname,
                    "ssid": ssid,
                    "band": band,
                    "channel": channel,
                    "priority": priority,
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
                group.setDetail("priority", network["priority"], "hidden")
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
            self.next_run[openwrt_ip]["wifi_clients"] = datetime.now()
            
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
        
    def _processWifiClients(self, openwrt_ip, ubus_session_id, events, openwrt_mac):
        self.next_run[openwrt_ip]["wifi_clients"] = datetime.now() + timedelta(seconds=self.config.openwrt_client_interval)

        client_results = []
        for wlan_network in list(self.wifi_networks[openwrt_ip].values()):
            try:
                client_result = self._getWifiClients(openwrt_ip, ubus_session_id, wlan_network["ifname"])
            except UbusCallException as e:
                if e.getCode() == -32000:
                    logging.warning("OpenWRT '{}' interface '{}' has gone".format(openwrt_ip, wlan_network["ifname"]))
                    
                    # force refresh for wifi networks & clients
                    self.next_run[openwrt_ip]["wifi_networks"] = datetime.now()
                else:
                    raise e
            client_results.append([client_result,wlan_network])
                
        if client_results or self.wifi_associations[openwrt_ip]:
            self.cache.lock(self)

            #with cProfile.Profile() as pr:
            now = datetime.now()

            _active_client_macs = []
            _active_associations = []
            for [client_result,wlan_network] in client_results:
                #logging.info(client_result)
                for mac in client_result["clients"]:
                    if mac == self.cache.getGatewayMAC():
                        continue
                                
                    target_mac = openwrt_mac
                    target_interface = mac
                    vlan = wlan_network["vlan"]
                    gid = wlan_network["gid"]
                    band = wlan_network["band"]
                    
                    uid = "{}-{}".format(mac, gid)
                    
                    connection_details = { "vlan": vlan, "band": band }

                    device = self.cache.getDevice(mac)
                    device.cleanDisabledHobConnections(target_mac, lambda event: events.append(event))
                    device.addHopConnection(Connection.WIFI, target_mac, target_interface, connection_details );
                    device.addGID(gid)
                    self.cache.confirmDevice( device, lambda event: events.append(event) )

                    details = client_result["clients"][mac]
                
                    stat = self.cache.getConnectionStat(target_mac,target_interface)
                    stat_data = stat.getData(connection_details)
                    if not details["assoc"]: 
                        stat_data.reset()
                    else:
                        if uid in self.wifi_associations[openwrt_ip]:
                            time_diff = (now - self.wifi_associations[openwrt_ip][uid][0]).total_seconds()

                            in_bytes = stat_data.getInBytes()
                            if in_bytes is not None:
                                byte_diff = details["bytes"]["rx"] - in_bytes
                                if byte_diff > 0:
                                    stat_data.setInAvg(byte_diff / time_diff)
                                
                            out_bytes = stat_data.getOutBytes()
                            if out_bytes is not None:
                                byte_diff = details["bytes"]["tx"] - out_bytes
                                if byte_diff > 0:
                                    stat_data.setOutAvg(byte_diff / time_diff)

                        stat_data.setInBytes(details["bytes"]["rx"])
                        stat_data.setOutBytes(details["bytes"]["tx"])
                        stat_data.setInSpeed(details["rate"]["rx"] * 1000)
                        stat_data.setOutSpeed(details["rate"]["tx"] * 1000)
                        stat_data.setDetail("signal", details["signal"], "attenuation")
                    self.cache.confirmStat( stat, lambda event: events.append(event) )
                        
                    _active_associations.append(uid)
                    self.wifi_associations[openwrt_ip][uid] = [ now, uid, mac, gid, vlan, target_mac, target_interface, connection_details ]

                    _active_client_macs.append(mac)
                    self.wifi_clients[openwrt_ip][mac] = True
                    
            for [ _, uid, mac, gid, vlan, target_mac, target_interface, connection_details ] in list(self.wifi_associations[openwrt_ip].values()):
                if uid not in _active_associations:
                    device = self.cache.getDevice(mac)
                    device.removeGID(gid);
                    # **** connection cleanup and stats cleanup happens in cleanDisabledHobConnection ****
                    device.disableHopConnection(Connection.WIFI, target_mac, target_interface)
                    self.cache.confirmDevice( device, lambda event: events.append(event) )

                    self.cache.removeConnectionStatDetails(target_mac,target_interface,connection_details, lambda event: events.append(event))
                    
                    del self.wifi_associations[openwrt_ip][uid]
                    
                    if mac not in _active_client_macs:
                        del self.wifi_clients[openwrt_ip][mac]

            #sortby = SortKey.CUMULATIVE
            #ps = pstats.Stats(pr).sort_stats(sortby)
            #ps.print_stats()
                    
            self.cache.unlock(self)

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
        start = datetime.now()
        r = self._post(ip, json)
        Helper.logProfiler(self, start, "Session of '{}' refreshed".format(ip))
        return self._parseResult(ip, r, "session")
    
    def _getDevices(self, ip, session ):
        json = { "jsonrpc": "2.0", "id": 1, "method": "call", "params": [ session, "network.device", "status", {} ] }
        start = datetime.now()
        r = self._post(ip, json)
        Helper.logProfiler(self, start, "Devices of '{}' fetched".format(ip))
        return self._parseResult(ip, r, "device_list")

    def _getWifiNetworks(self, ip, session ):
        json = { "jsonrpc": "2.0", "id": 1, "method": "call", "params": [ session, "network.wireless", "status", {} ] }
        start = datetime.now()
        r = self._post(ip, json)
        Helper.logProfiler(self, start, "Networks of '{}' fetched".format(ip))
        return self._parseResult(ip, r, "device_list")

    def _getWifiInterfaceDetails(self, ip, session, interface ):
        json = { "jsonrpc": "2.0", "id": 1, "method": "call", "params": [ session, "hostapd.{}".format(interface), "get_status", {} ] }
        start = datetime.now()
        r = self._post(ip, json)
        Helper.logProfiler(self, start, "Network details of '{}' fetched".format(ip))
        return self._parseResult(ip, r, "device_details")

    def _getWifiClients(self, ip, session, interface ):
        json = { "jsonrpc": "2.0", "id": 1, "method": "call", "params": [ session, "hostapd.{}".format(interface), "get_clients", {} ] }
        start = datetime.now()
        r = self._post(ip, json)
        Helper.logProfiler(self, start, "Clients of '{}' fetched".format(ip))
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
                    self.next_run[openwrt_ip]["wifi_clients"] = datetime.now()
                    triggered_types["wifi"] = True
                    
            if triggered_types:
                logging.info("Delayed trigger runs for {}".format(" & ".join(triggered_types)))

                self._wakeup()
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
