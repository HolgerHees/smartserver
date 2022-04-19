import threading
from datetime import datetime, timedelta
import re
import requests
import json
import traceback
import math

from smartserver import command

from lib.watcher import watcher
from lib.dto.device import Device
from lib.dto.stats import Stats
from lib.dto.event import Event
from lib.helper import Helper


class LibreNMS(watcher.Watcher): 
    def __init__(self, logger, config, handler ):
        super().__init__(logger)
      
        self.logger = logger
        self.config = config
        self.handler = handler
        
        self.is_running = True
        
        self.port_id_name_map = {}
        
        self.last_check = {"device": 0, "port": 0, "fdb": 0}
        
        self.devices = {}

        self.connected_arps = {}
        self.port_connection_stats = {}
        self.port_connection_stats_refresh = {}
        
        self.condition = threading.Condition()
        self.thread = threading.Thread(target=self.checkLibreNMS, args=())
        
        self.data_lock = threading.Lock()

    def start(self):
        self.thread.start()
        
    def terminate(self):
        with self.condition:
            self.is_running = False
            self.condition.notifyAll()

    def checkLibreNMS(self):
        suspend_timeout = 0
        while self.is_running:
            now = datetime.now().timestamp()
            #RequestHeader set "X-Auth-Token" "{{vault_librenms_api_token}}"
            
            changes = {}
            
            timeout = 100000000
            
            if suspend_timeout < now:
                try:
                    timeout = self._processLibreNMS(now, changes, timeout)
                except requests.exceptions.ConnectionError:
                    self.logger.warning("LibreNMS currently not available. Will suspend for 5 minutes")
                    suspend_timeout = now + self.config.librenms_suspend_timeout
                    if timeout > self.config.librenms_suspend_timeout:
                        timeout = self.config.librenms_suspend_timeout
                except Exception as e:
                    self.logger.error("LibreNMS got unexpected exception. Will suspend for 15 minutes.")
                    self.logger.error(traceback.format_exc())
                    if timeout > self.config.librenms_error_timeout:
                        timeout = self.config.librenms_error_timeout
                        
                events = self._prepareEvents(changes)
                if len(events) > 0:
                    self.handler.notify(self,events)

                if timeout > 0:
                    with self.condition:
                        self.condition.wait(timeout)
                    
    def _processLibreNMS(self, now, changes, timeout):
        if now - self.last_check["device"] >= self.config.librenms_device_interval:
            [timeout, self.last_check["device"]] = self._getDevices(now, changes, timeout, self.config.librenms_device_interval)
                                        
        if now - self.last_check["port"] >= self.config.librenms_port_interval:
            self.last_check["port"] = now
            if timeout > self.config.librenms_port_interval:
                timeout = self.config.librenms_port_interval

            _ports_json = self._get("ports?columns=device_id,ifIndex,ifName,ifInOctets,ifOutOctets,ifSpeed,ifDuplex")
            _ports = json.loads(_ports_json)["ports"]
            _active_ports = {}
            for _port in _ports:
                if _port["device_id"] not in self.devices:
                    [timeout, self.last_check["device"]] = self._getDevices(now, changes, timeout, self.config.librenms_device_interval)
                    
                    if _port["device_id"] not in self.devices:
                        self.logger.error("LibreNMS device id '{}' not found".format(_port["device_id"])) 
                        continue

                with self.data_lock:
                    ip = self.devices[_port["device_id"]]["ip"]
                    port = _port["ifName"]
                    
                    if ip not in _active_ports:
                        _active_ports[ip] = []
                    _active_ports[ip].append(port)
                    
                    in_avg = 0
                    out_avg = 0
                    if ip in self.port_connection_stats and port in self.port_connection_stats[ip]:
                        _port_connection_stats = self.port_connection_stats[ip][port]
                        time_diff = (now - self.port_connection_stats_refresh[ip][port])
                        time_diff_slot = math.ceil(time_diff / self.config.librenms_poller_interval)
                        time_diff = time_diff_slot * self.config.librenms_poller_interval
                        
                        in_diff = _port["ifInOctets"] - _port_connection_stats["in_traffic"]
                        if in_diff < 0: # => counter overflow
                            in_avg = _port_connection_stats["in_avg"]
                        elif in_diff == 0 and time_diff < self.config.librenms_poller_interval * 2:
                            in_avg = _port_connection_stats["in_avg"]
                        else:
                            in_avg = in_diff / time_diff

                        out_diff = _port["ifOutOctets"] - _port_connection_stats["out_traffic"]
                        if out_diff < 0: # => counter overflow
                            out_avg = _port_connection_stats["out_avg"]
                        elif out_diff == 0 and time_diff < self.config.librenms_poller_interval * 2:
                            out_avg = _port_connection_stats["out_avg"]
                        else:
                            out_avg = in_diff / time_diff
                        
                    port_connection_stat = {
                        "ip": ip,
                        "port": port,
                        "in_traffic": _port["ifInOctets"],
                        "in_avg": in_avg,
                        "out_traffic": _port["ifOutOctets"],
                        "out_avg": out_avg,
                        "in_speed": _port["ifSpeed"],
                        "out_speed": _port["ifSpeed"],
                        "duplex": "full" if _port["ifDuplex"] == "fullDuplex" else "half"
                    }
                    
                    if ip not in self.port_connection_stats:
                        self.port_connection_stats[ip] = {}
                        self.port_connection_stats_refresh[ip] = {}
                    
                    if port not in self.port_connection_stats[ip] or not self.data_equal(self.port_connection_stats[ip][port], port_connection_stat):
                        self._appendChange(changes, Event.TYPE_PORT_STAT, "{}:{}".format(ip,port), {"action": "change", "stat": port_connection_stat})
                        self.port_connection_stats[ip][port] = port_connection_stat
                        self.port_connection_stats_refresh[ip][port] = now

                    if ip not in self.port_id_name_map:
                        self.port_id_name_map[ip] = {0: "lo"}
                    self.port_id_name_map[ip][_port["ifIndex"]] = _port["ifName"]
                    
            with self.data_lock:
                for ip in list(self.port_connection_stats.keys()):
                    if ip not in _active_ports:
                        self.logger.info("Clean ports '{}'".format(ip))
                        for port in list(self.port_connection_stats[ip]):
                            self._appendChange(changes, Event.TYPE_PORT_STAT, "{}:{}".format(ip,port), {"action": "delete", "stat": self.port_connection_stats[ip][port]})
                        del self.port_connection_stats[ip]
                        del self.port_connection_stats_refresh[ip]
                    else:
                        for port in list(self.port_connection_stats[ip]):
                            if port not in _active_ports[ip]:
                                self.logger.info("Clean port '{}:{}'".format(ip,port))
                                self._appendChange(changes, Event.TYPE_PORT_STAT, "{}:{}".format(ip,port), {"action": "delete", "stat": self.port_connection_stats[ip][port]})
                                del self.port_connection_stats[ip][port]
                                del self.port_connection_stats_refresh[ip][port]
            
        if now - self.last_check["fdb"] >= self.config.librenms_fdb_interval:
            self.last_check["fdb"] = now
            if timeout > self.config.librenms_fdb_interval:
                timeout = self.config.librenms_fdb_interval
                
            _connected_arps_json = self._get("resources/fdb")
            _connected_arps = json.loads(_connected_arps_json)["ports_fdb"]
            _active_connected_macs = []
            with self.data_lock:
                for _connected_arp in _connected_arps:
                    target_mac = self.devices[_connected_arp["device_id"]]["mac"]
                    target_ip = self.devices[_connected_arp["device_id"]]["ip"]

                    _mac = _connected_arp["mac_address"]
                    mac = ":".join([_mac[i:i+2] for i in range(0, len(_mac), 2)])
                    _active_connected_macs.append(mac)
                    
                    connected_arp = {
                        "source_mac": mac,        # e.g. client device
                        "target_mac": target_mac, # e.g. switch device
                        "target_port": self.port_id_name_map[target_ip][_connected_arp["port_id"]],
                        "vlan_id": _connected_arp["vlan_id"]
                    }
                    
                    if mac not in self.connected_arps or not self.data_equal(self.connected_arps[mac], connected_arp):
                        self.connected_arps[mac] = connected_arp
                        self.last_connected_arps_refresh = round(now,3)
                        self._appendChange(changes, Event.TYPE_DEVICE, mac, { "connection_action": "change", "connection": connected_arp } )
                        
                for mac in list(self.connected_arps):
                    if mac not in _active_connected_macs:
                        self.logger.info("Clean mac '{}'".format(mac))
                        self._appendChange(changes, Event.TYPE_DEVICE, mac, { "connection_action": "delete", "connection": self.connected_arps[mac] } )
                        del self.connected_arps[mac]
                
        return timeout
                
    def _getDevices(self, now, changes, global_timeout, call_timeout):
        _device_json = self._get("devices")
        _devices = json.loads(_device_json)["devices"]
        _current_device_ids = []
        with self.data_lock:
            for _device in _devices:
                mac = Helper.ip2mac(_device["hostname"])
                device = {
                    "mac": mac,
                    "ip": _device["hostname"],
                    "id": _device["device_id"],
                    "hardware": _device["hardware"],
                    "type": _device["type"]
                }
                _current_device_ids.append(device["id"])
            
                if _device["device_id"] not in self.devices or not self.data_equal(self.devices[_device["device_id"]], device):
                    self._appendChange(changes, Event.TYPE_DEVICE, mac, { "device_action": "change", "device": device })
                    self.devices[_device["device_id"]] = device
                        
            for id in list(self.devices):
                if id not in _current_device_ids:
                    self.logger.info("Clean device '{}'".format(id))
                    self._appendChange(changes, Event.TYPE_DEVICE, mac, { "device_action": "delete", "device": self.devices[id] } )
                    del self.devices[id]
            
        if global_timeout > call_timeout:
            global_timeout = call_timeout

        return [global_timeout, now]
                
    def _get(self,call):
        headers = {'X-Auth-Token': self.config.librenms_token}
        
        #print("{}{}".format(self.config.librenms_rest,call))
        r = requests.get( "{}{}".format(self.config.librenms_rest,call), headers=headers)
        return r.text
    
    def triggerEvents(self, groups, devices, stats, events):
        for event in events:
            if event.getType() != Event.TYPE_DEVICE:
                continue
            
            if event.getAction() != Event.ACTION_CREATE:
                with self.data_lock:
                    mac =  event.getIdentifier()

                    # check if created mac is related to librenms devices
                    _devices = list(filter(lambda d: d["mac"] == mac, self.devices.values() ))
                    if len(_devices) == 0:
                        continue
                    _device = _devices[0]

                    device = list(filter(lambda d: d.getMAC() == mac, devices ))[0]
                    self._fillDevice(device, _device, True)
                        
                    _connected_arps = list(filter(lambda a: a["source_mac"] == mac or a["target_mac"] == mac, self.connected_arps.values() ))
                    for _connected_arp in _connected_arps:
                        self._fillConnection(_connected_arp, devices, True)

            elif event.getAction() != Event.ACTION_MODIFY:
                with self.data_lock:
                    # fill fallback connections
                    _connected_arps = list(filter(lambda a: a["source_mac"] == event.getIdentifier(), self.connected_arps.values() ))
                    for _connected_arp in _connected_arps:
                        self._fillConnection(_connected_arp, devices, True)

    def processEvents(self, groups, devices, stats, events):
        with self.data_lock:
            for event in events:
                if event.getType() == Event.TYPE_DEVICE:
                    mac = event.getIdentifier()

                    # check if librenms mac is existing in global devices
                    _devices = list(filter(lambda d: d.getMAC() == mac, devices ))
                    if len(_devices) == 0:
                        continue
                    device = _devices[0]
                    
                    device_action = event.getPayload("device_action")
                    if device_action is not None:
                        if device_action == "delete":
                            if self._cleanDevice(device):
                                event.setAction(Event.ACTION_MODIFY)
                        else:
                            _device = event.getPayload("device")
                            if self._fillDevice(device, _device, False):
                                event.setAction(Event.ACTION_MODIFY)
                    
                    connection_action = event.getPayload("connection_action")
                    if connection_action is not None:
                        if connection_action == "delete":
                            if self._cleanConnection(device):
                                event.setAction(Event.ACTION_MODIFY)
                        else:
                            _connected_arp = event.getPayload("connection")
                            if self._fillConnection(_connected_arp, devices, False):
                                event.setAction(Event.ACTION_MODIFY)

                elif event.getType() == Event.TYPE_PORT_STAT:
                    key = event.getIdentifier()

                    #[ip, port] = key.split(":")

                    if event.getPayload("action") == "delete":
                        for stat in list(filter(lambda d: d.getTarget() == key, stats )):
                            stats.remove(stat)

                            self.logger.info("Clean stats {}".format(stat))
                            event.setAction(Event.ACTION_DELETE)
                    else:
                        _stats = list(filter(lambda s: s.getTarget() == key, stats ))
                        if len(_stats) > 0:
                            stat = _stats[0]

                            self.logger.info("Update stats {}".format(stat))
                            event.setAction(Event.ACTION_MODIFY)
                        else:                  
                            stat = Stats(key, "port")
                            stats.append(stat)
                    
                            self.logger.info("Add stats {}".format(stat))
                            event.setAction(Event.ACTION_CREATE)

                        _stat = event.getPayload("stat")
                        
                        stat.setInBytes(_stat["in_traffic"])
                        stat.setInAvg(_stat["in_avg"])
                        stat.setOutBytes(_stat["out_traffic"])
                        stat.setOutAvg(_stat["out_avg"])
                        stat.setInSpeed(_stat["in_speed"])
                        stat.setOutSpeed(_stat["out_speed"])

                        stat.appendDetails("duplex", _stat["duplex"])
    
    def _cleanDevice(self, device ):
        device.resetPorts()
        device.removeDetail("hardware");
        device.setType(None)
        
        self.logger.info("Clean device {}".format(device))
        
        return True

    def _fillDevice(self, device, _device, is_lazy ):
        ports = self.port_id_name_map[device.getIp()]
        for port_id in ports:
            device.setPort(port_id, ports[port_id])
        device.setDetail("hardware",_device["hardware"]);
        device.setType(_device["type"]);
            
        self.logger.info("Update{} device {}".format(" lazy" if is_lazy else "", device))

        return True
    
    def _cleanConnection(self, device ):
        self.logger.info("Clean connection from {} to {}".format(device, device.getConnectionTargetUID()))

        device.removeConnectionTarget(Device.CONNECTION_TYPE_ETHERNET)

        return True
    
    def _fillConnection(self, _connected_arp, devices, is_lazy ):
        _source_devices = list(filter(lambda d: d.getMAC() == _connected_arp["source_mac"], devices ))
        if len(_source_devices) == 0:
            #self.logger.info("Can't update unknown from device '{}'".format(mac))
            return False
        _source_device = _source_devices[0]

        if _source_device.getConnectionTargetUID() is None or _source_device.getConnectionType() == Device.CONNECTION_TYPE_ETHERNET:
            _target_devices = list(filter(lambda d: d.getMAC() == _connected_arp["target_mac"], devices ))
            _target = _target_devices[0] if len(_target_devices) > 0 else _connected_arp["target_mac"]

            self.logger.info("Update{} connection from {} to {}".format(" lazy" if is_lazy else "", _source_device, _target ) )

            _source_device.setConnectionTarget( _connected_arp["target_mac"], _connected_arp["target_port"], _connected_arp["vlan_id"], Device.CONNECTION_TYPE_ETHERNET );

        return True
