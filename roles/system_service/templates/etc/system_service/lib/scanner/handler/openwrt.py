import threading
from datetime import datetime, timedelta
import time
import requests
from urllib3.exceptions import InsecureRequestWarning
import json
import logging
import re
#import cProfile, pstats
#from pstats import SortKey

from smartserver import command

from lib.scanner.handler import _handler
from lib.scanner.dto._changeable import Changeable
from lib.scanner.dto.device import Device, Connection
from lib.scanner.dto.group import Group
from lib.scanner.dto.event import Event
from lib.scanner.helper import Helper


class OpenWRT(_handler.Handler): 
    def __init__(self, config, cache, openwrt_devices ):
        super().__init__(config,cache)
        
        self.openwrt_devices = openwrt_devices

        self.sessions = {}
        
        self.next_run = {}
        
        self.devices = {}

        self.active_vlans = {}

        self.has_wifi_networks = False
        self.wifi_networks = {}

        self.wifi_associations = {}
        self.wifi_clients = {}

        self.delayed_lock = threading.Lock()
        self.delayed_wifi_devices = {}
        self.delayed_wakeup_timer = None

        requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

    def _initNextRuns(self, limit_openwrt_ip = None):
        now = datetime.now()
        for openwrt_ip in self.openwrt_devices:
            if limit_openwrt_ip is not None and limit_openwrt_ip != openwrt_ip:
                continue
            self.sessions[openwrt_ip] = [ None, datetime.now()]
            self.next_run[openwrt_ip] = {"interfaces": now, "wifi_networks": now, "wifi_clients": now}

    def _run(self):
        self._initNextRuns()

        for openwrt_ip in self.openwrt_devices:
            self.active_vlans[openwrt_ip] = {}

            self.wifi_networks[openwrt_ip] = {}

            self.wifi_associations[openwrt_ip] = {}
            self.wifi_clients[openwrt_ip] = {}

            self._setDeviceMetricState(openwrt_ip, -1)

        while self._isRunning():
            #RequestHeader set "X-Auth-Token" "{{vault_librenms_api_token}}"
            
            for openwrt_ip in self.openwrt_devices:
                try:
                    if self._isSuspended(openwrt_ip):
                        continue
                    
                    session_retries = 1
                    while True:
                        try:
                            self._processDevice(openwrt_ip)
                        except UbusCallException as e:
                            if session_retries > 0 and self.sessions[openwrt_ip][0] is not None and e.getCode() == -32002:
                                logging.info("OpenWRT '{}' has invalid session. Will refresh.".format(openwrt_ip))
                                
                                self._initNextRuns(openwrt_ip)
                                self.cache.cleanLocks(self)

                                session_retries -= 1
                            else:
                                raise e
                        break

                    self._setDeviceMetricState(openwrt_ip, 1)
                except UbusCallException as e:
                    self._initNextRuns(openwrt_ip)
                    self.cache.cleanLocks(self)

                    self._handleExpectedException("OpenWRT '{}' ({})' got exception {} - '{}'".format(openwrt_ip, e.getType(), e.getCode(), e), openwrt_ip, self.config.remote_error_timeout)
                    self._setDeviceMetricState(openwrt_ip, 0)
                except NetworkException as e:
                    self._initNextRuns(openwrt_ip)
                    self.cache.cleanLocks(self)

                    self._handleExpectedException(str(e), openwrt_ip, e.getTimeout())
                    self._setDeviceMetricState(openwrt_ip, 0)
                except Exception as e:
                    self._initNextRuns(openwrt_ip)
                    self.cache.cleanLocks(self)

                    self._handleUnexpectedException(e, openwrt_ip)
                    self._setDeviceMetricState(openwrt_ip, -1)
                
            timeout = 9999999999
            now = datetime.now()
            for openwrt_ip in self.openwrt_devices:
                suspend_timeout = self._getSuspendTimeout(openwrt_ip)
                if suspend_timeout > 0:
                    if suspend_timeout < timeout:
                        timeout = suspend_timeout
                else:
                    for next_run in self.next_run[openwrt_ip].values():
                        diff = (next_run - now).total_seconds()
                        if diff < timeout:
                            timeout = diff
                        
            if timeout > 0:
                self._wait(timeout)
                                        
    def _processDevice(self, openwrt_ip ):
        openwrt_mac = self.cache.ip2mac(openwrt_ip, self._isRunning)
        if openwrt_mac is None:
            raise NetworkException("OpenWRT '{}' not resolvable".format(openwrt_ip), 15)

        if datetime.now() >= self.sessions[openwrt_ip][1]:
            result = self._getSession( openwrt_ip, self.config.openwrt_username, self.config.openwrt_password )
            self.sessions[openwrt_ip] = [ result["ubus_rpc_session"], datetime.now() + timedelta(seconds=result["expires"] - 10 ) ];

        if self.sessions[openwrt_ip][0] is None:
            return self.sessions[openwrt_ip][1] - now
        
        ubus_session_id = self.sessions[openwrt_ip][0]
                            
        if self.next_run[openwrt_ip]["interfaces"] <= datetime.now():
            self._processInterfaces(openwrt_ip, ubus_session_id, openwrt_mac)

        if self.next_run[openwrt_ip]["wifi_networks"] <= datetime.now():
            self._processWifiNetworks(openwrt_ip, ubus_session_id, openwrt_mac)
                            
        if self.next_run[openwrt_ip]["wifi_clients"] <= datetime.now():  
            self._processWifiClients(openwrt_ip, ubus_session_id, openwrt_mac)
                
    def _processInterfaces(self, openwrt_ip, ubus_session_id, openwrt_mac):
        now = datetime.now()
        is_gateway = openwrt_mac == self.cache.getGatewayMAC()

        self.next_run[openwrt_ip]["interfaces"] = now + timedelta(seconds=self.config.openwrt_client_interval if is_gateway else self.config.openwrt_network_interval)

        self.cache.lock(self)

        if is_gateway:
            openhab_device = self.cache.getDevice(openwrt_mac)
            openhab_device.addHopConnection(Connection.ETHERNET, self.cache.getWanMAC(), self.cache.getWanInterface() );
            self.cache.confirmDevice( self, openhab_device )

        _active_vlans = {}
        _interfaces = {}
        device_result = self._getDevices(openwrt_ip, ubus_session_id)

        wan_stats = { "max_up": 0, "max_down": 0, "sum_sent": 0, "sum_received": 0 }
        lan_stats = { "max_up": 0, "max_down": 0, "sum_sent": 0, "sum_received": 0 }

        for device_name in device_result:
            _device = device_result[device_name]

            if is_gateway:
                if device_name[0:3] == "br-" and not re.match(".*\.[0-9]+$", device_name) and "speed" in _device:
                    #logging.info("LANCHECK {}".format(device_name))

                    is_wan = True if device_name == "br-wan" else False
                    _ref = wan_stats if is_wan else lan_stats

                    #logging.info(_device)
                    #logging.info(is_wan)
                    #logging.info(_ref)

                    speed = _device["speed"][:-1]
                    if _ref["max_up"] < int(speed):
                        _ref["max_up"] = int(speed)
                        _ref["max_down"] = int(speed)

                    _ref["sum_sent"] += int(_device["statistics"]["tx_bytes"])
                    _ref["sum_received"] += int(_device["statistics"]["rx_bytes"])

                    #logging.info(str(stat.getSerializeable()))

            if "bridge-vlans" in _device:
                for vlan in _device["bridge-vlans"]:
                    for port in vlan["ports"]:
                        _active_vlans[port] = vlan["id"]

        if is_gateway:
            for is_wan in [True,False]:
                #link_state = {'up': int(speed), 'down': int(speed)}
                #traffic_state = {'sent': int(_device["statistics"]["tx_bytes"]), 'received': int(_device["statistics"]["rx_bytes"])}

                _ref = wan_stats if is_wan else lan_stats

                if is_wan:
                    stat = self.cache.getConnectionStat(self.cache.getWanMAC(), self.cache.getWanInterface() )
                    stat_data = stat.getData()
                    stat_data.setDetail("wan_type","Ethernet", "string")
                    stat_data.setDetail("wan_state","Up" if _device["up"] else "Down", "string")
                else:
                    stat = self.cache.getConnectionStat(openwrt_mac, self.cache.getGatewayInterface(self.config.default_vlan) )
                    stat_data = stat.getData()

                interface = "wan" if is_wan else "lan"

                if openwrt_ip in self.devices and interface in self.devices[openwrt_ip]:
                    time_diff = (now - self.devices[openwrt_ip][interface]).total_seconds()

                    in_bytes = stat_data.getInBytes()
                    if in_bytes is not None:
                        byte_diff = _ref["sum_received"] - in_bytes
                        if byte_diff > 0:
                            stat_data.setInAvg(byte_diff / time_diff)

                    out_bytes = stat_data.getOutBytes()
                    if out_bytes is not None:
                        byte_diff = _ref["sum_sent"] - out_bytes
                        if byte_diff > 0:
                            stat_data.setOutAvg(byte_diff / time_diff)

                stat_data.setInBytes(_ref["sum_received"])
                stat_data.setOutBytes(_ref["sum_sent"])
                stat_data.setInSpeed(_ref["max_down"] * 1000000)
                stat_data.setOutSpeed(_ref["max_up"] * 1000000)
                self.cache.confirmStat( self, stat )

                _interfaces[interface] = now

        self.cache.unlock(self)

        self.devices[openwrt_ip] = _interfaces

        self.active_vlans[openwrt_ip] = _active_vlans

    def _processWifiNetworks(self, openwrt_ip, ubus_session_id, openwrt_mac):
        self.next_run[openwrt_ip]["wifi_networks"] = datetime.now() + timedelta(seconds=self.config.openwrt_network_interval)

        wifi_network_result = self._getWifiNetworks(openwrt_ip, ubus_session_id)
        if wifi_network_result is None:
            self.wifi_networks[openwrt_ip] = {}
        else:
            wifi_network_changed = False

            _active_networks = {}
            for wifi_network_name in wifi_network_result:
                _wifi_network = wifi_network_result[wifi_network_name]
                for _interface in _wifi_network["interfaces"]:
                    # skip non configured interfaces
                    if "ifname" not in _interface:
                        continue

                    ifname = _interface["ifname"];
                    ssid = _interface["config"]["ssid"];
                    band = _wifi_network["config"]["band"];
                    gid = "{}-{}-{}".format(openwrt_ip,ssid,band)

                    try:
                        wifi_interface_details_result = self._getWifiInterfaceDetails(openwrt_ip, ubus_session_id, ifname)
                    except UbusCallException as e:
                        if e.getCode() == -32000:
                            logging.warning("OpenWRT '{}' interface '{}' has gone during processing wifi networks".format(openwrt_ip, ifname))
                            continue
                        else:
                            raise e

                    channel = wifi_interface_details_result["channel"]
                    priority = 1 if channel > 13 else 0

                    network = {
                        "gid": gid,
                        "ifname": ifname,
                        "ssid": ssid,
                        "band": band,
                        "channel": channel,
                        "priority": priority,
                        "vlan": self.active_vlans[openwrt_ip][ifname] if ifname in self.active_vlans[openwrt_ip] else self.config.default_vlan,
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
                    self.cache.confirmGroup(self, group)

                for gid in list(self.wifi_networks[openwrt_ip].keys()):
                    if gid not in _active_networks:
                        wifi_network_changed = True

                        self.cache.removeGroup(self, gid)
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
            self.cache.confirmDevice( self, device )
            self.cache.unlock(self)

        has_wifi_networks = False
        for _openwrt_ip in self.openwrt_devices:
            if self.wifi_networks[_openwrt_ip]:
                has_wifi_networks = True
                break
        self.has_wifi_networks = has_wifi_networks
        
    def _processWifiClients(self, openwrt_ip, ubus_session_id, openwrt_mac):
        self.next_run[openwrt_ip]["wifi_clients"] = datetime.now() + timedelta(seconds=self.config.openwrt_client_interval)

        client_results = []
        for wlan_network in list(self.wifi_networks[openwrt_ip].values()):
            try:
                client_result = self._getWifiClients(openwrt_ip, ubus_session_id, wlan_network["ifname"])
                client_results.append([client_result,wlan_network])
            except UbusCallException as e:
                if e.getCode() == -32000:
                    logging.warning("OpenWRT '{}' interface '{}' has gone during processing wifi clients".format(openwrt_ip, wlan_network["ifname"]))
                    # force refresh for wifi networks & clients
                    self.next_run[openwrt_ip]["wifi_networks"] = datetime.now()
                else:
                    raise e
                
        if client_results or self.wifi_associations[openwrt_ip]:
            self.cache.lock(self)

            #with cProfile.Profile() as pr:
            now = datetime.now()

            _active_client_macs = []
            _active_associations = []

            events = []
            for [client_result,wlan_network] in client_results:
                #logging.info(client_result)
                for mac in client_result["clients"]:
                    if mac == self.cache.getGatewayMAC():
                        continue


                                
                    vlan = wlan_network["vlan"]
                    gid = wlan_network["gid"]
                    band = wlan_network["band"]
                    
                    target_mac = openwrt_mac
                    target_interface = mac

                    uid = "{}-{}-{}".format(mac, target_mac, gid)
                    
                    connection_details = { "vlan": vlan, "gid": gid }

                    device = self.cache.getDevice(mac)
                    device.addHopConnection(Connection.WIFI, target_mac, target_interface, connection_details );
                    event = self.cache.confirmDevice( self, device )
                    if event:
                        events.append(event)

                    details = client_result["clients"][mac]

                    # mark as online for new clients or if it is not a user device (is checked in arpscan)
                    if mac not in self.wifi_clients[openwrt_ip] or device.getIP() is None or device.getIP() not in self.config.user_devices:
                        stat = self.cache.getDeviceStat(mac)
                        stat.setLastSeen(False) # because no IP validation
                        if details["auth"] and details["assoc"] and details["authorized"]:
                            stat.setOnline(True)
                        event = self.cache.confirmStat( self, stat )
                        if event:
                            events.append(event)

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
                    event = self.cache.confirmStat( self, stat )
                    if event:
                        if device.hasMultiConnections():
                            device.generateMultiConnectionEvents(event,events)
                        events.append(event)
                    
                    _active_associations.append(uid)
                    self.wifi_associations[openwrt_ip][uid] = [ now, uid, mac, gid, vlan, target_mac, target_interface, connection_details ]

                    _active_client_macs.append(mac)
                    self.wifi_clients[openwrt_ip][mac] = True
                    
            for [ _, uid, mac, gid, vlan, target_mac, target_interface, connection_details ] in list(self.wifi_associations[openwrt_ip].values()):
                if uid not in _active_associations:
                    device = self.cache.getUnlockedDevice(mac)
                    if device is not None:
                        device.lock(self)
                        device.removeHopConnection(Connection.WIFI, target_mac, target_interface, connection_details, True)
                        self.cache.confirmDevice( self, device )

                    self.cache.removeConnectionStatDetails(self, target_mac,target_interface,connection_details)
                    
                    del self.wifi_associations[openwrt_ip][uid]
                    
                    if mac not in _active_client_macs and mac in self.wifi_clients[openwrt_ip]:
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

        return result["result"][1] if len(result["result"]) > 1 else None
        #logging.warning("OpenWRT {} - {} - got unexpected device result '{}'".format(ip, type, _json))
        #return None
    
    def _post(self, ip, json, retry=1):
        try:
            return requests.post( "https://{}/ubus".format(ip), json=json, verify=False)
        except requests.exceptions.ConnectionError as e:
            msg = "OpenWRT {} currently not available".format(ip)
            if retry > 0: 
                logging.info(msg)
                for i in range(3):
                    if Helper.ping(ip, 5, self._isRunning): # ubus calls are sometimes (~ones every 2 days) answered with a 500
                        logging.info(str(e))
                        logging.info("Retry connecting {}".format(ip))
                        return self._post(ip, json, retry - 1)
                    else:
                        logging.info("{}. retry connecting {} in 5 seconds.".format(i + 1, ip))
                        time.sleep(5)
            raise NetworkException(msg, self.config.remote_suspend_timeout)
        
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
        return self._parseResult(ip, r, "device_details of '{}'".format(interface))

    def _getWifiClients(self, ip, session, interface ):
        json = { "jsonrpc": "2.0", "id": 1, "method": "call", "params": [ session, "hostapd.{}".format(interface), "get_clients", {} ] }
        start = datetime.now()
        r = self._post(ip, json)
        Helper.logProfiler(self, start, "Clients of '{}' fetched".format(ip))
        return self._parseResult(ip, r, "client_list of '{}'".format(interface))
    
    def _isKnownWifiClient(self, mac):
        for openwrt_ip in self.openwrt_devices:
            if mac in self.wifi_clients[openwrt_ip]:
                return True
        return False
    
    def _delayedWakeup(self):
        with self.delayed_lock:
            self.delayed_wakeup_timer = None
            
            missing_wifi_macs = []
            for mac in list(self.delayed_wifi_devices.keys()):
                if not self._isKnownWifiClient(mac):
                    missing_wifi_macs.append(mac)
                    
                del self.delayed_wifi_devices[mac]
            
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
        return [ { "types": [Event.TYPE_DEVICE_STAT], "actions": [Event.ACTION_MODIFY], "details": ["online_state"] } ]

    def processEvents(self, events):
        with self.delayed_lock:
            has_new_devices = False
            for event in events:
                stat = event.getObject()
                device = self.cache.getUnlockedDevice(stat.getMAC())
                if device is None:
                    logging.error("Unknown device for stat {}".format(stat))
                
                if not self.has_wifi_networks or not device.supportsWifi() or not stat.isOnline():
                    continue
                    
                self.delayed_wifi_devices[device.getMAC()] = device

                has_new_devices = True

                logging.info("Delayed trigger started for {}".format(device))
                    
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
    
    def getType(self):
        return self.type

class UbusResponseException(Exception):
    def __init__(self, ip, type, message):
        super().__init__(message)
            
        self.ip = ip
        self.type = type
