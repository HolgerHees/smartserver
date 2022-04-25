import threading
from datetime import datetime, timedelta
import re
import requests
import json
import traceback
import math
import logging

from smartserver import command

from lib.handler import _handler
from lib.dto._changeable import Changeable
from lib.dto.device import Device, Connection
from lib.dto.event import Event
from lib.helper import Helper


class LibreNMS(_handler.Handler): 
    def __init__(self, config, cache ):
        super().__init__()
      
        self.config = config
        self.cache = cache
        
        self.is_running = True
        
        self.last_check = {"device": 0, "vlan": 0, "port": 0, "fdb": 0}
        
        self.devices = {}
        
        self.device_ports = {}
        self.vlan_id_map = {}
        self.port_id_ifname_map = {}
        self.connected_macs = {}
        
        self.condition = threading.Condition()
        self.thread = threading.Thread(target=self._checkLibreNMS, args=())

    def start(self):
        self.thread.start()
        
    def terminate(self):
        with self.condition:
            self.is_running = False
            self.condition.notifyAll()

    def _checkLibreNMS(self):
        was_suspended = False

        while self.is_running:
            now = datetime.now().timestamp()
            #RequestHeader set "X-Auth-Token" "{{vault_librenms_api_token}}"
            
            events = []
            
            timeout = 100000000
            
            try:
                if was_suspended:
                    logging.warning("Resume LibreNMS")
                    was_suspended = False
                
                timeout = self._processLibreNMS(now, events, timeout)
            except NetworkException as e:
                logging.warning("{}. Will retry in 15 seconds.".format(e))
                if timeout > 15:
                    timeout = 15
            except requests.exceptions.ConnectionError:
                logging.warning("LibreNMS currently not available. Will suspend for 5 minutes")
                if timeout > self.config.remote_suspend_timeout:
                    timeout = self.config.remote_suspend_timeout
                was_suspended = True
            except Exception as e:
                logging.error("LibreNMS got unexpected exception. Will suspend for 15 minutes.")
                logging.error(traceback.format_exc())
                if timeout > self.config.remote_error_timeout:
                    timeout = self.config.remote_error_timeout
                was_suspended = True
                    
            if len(events) > 0:
                self._getDispatcher().dispatch(self,events)

            if timeout > 0:
                with self.condition:
                    self.condition.wait(timeout)
                    
    def _processLibreNMS(self, now, events, timeout):
        if now - self.last_check["device"] >= self.config.librenms_device_interval:
            [timeout, self.last_check["device"]] = self._processDevices(now, events, timeout, self.config.librenms_device_interval)
                                        
        if now - self.last_check["vlan"] >= self.config.librenms_vlan_interval:
            [timeout, self.last_check["vlan"]] = self._processVLANs(now, events, timeout, self.config.librenms_vlan_interval)

        if now - self.last_check["port"] >= self.config.librenms_port_interval:
            [timeout, self.last_check["port"]] = self._processPorts(now, events, timeout, self.config.librenms_port_interval)
    
        if now - self.last_check["fdb"] >= self.config.librenms_fdb_interval:               
            [timeout, self.last_check["fdb"]] = self._processFDP(now, events, timeout, self.config.librenms_fdb_interval)
            
        return timeout

    def _processDevices(self, now, events, global_timeout, call_timeout):
        
        _device_json = self._get("devices")
        _devices = json.loads(_device_json)["devices"]
        
        _active_devices = {}
        for _device in _devices:
            mac = self.cache.ip2mac(_device["hostname"])
            if mac is None:
                if device["id"] in self.devices:
                    mac = self.devices[device["id"]]["mac"]
                    logging.warning("Device {} currently not resolvable. User old mac address for now.".format(_device["hostname"]))
                else:
                    raise NetworkException("Device {} currently not resolvable".format(_device["hostname"]))
            
            device = {
                "mac": mac,
                "ip": _device["hostname"],
                "id": _device["device_id"],
                "hardware": _device["hardware"],
                "type": _device["type"]
            }
            _active_devices[device["id"]] = device
            self.devices[device["id"]] = device

        if _active_devices or self.devices:
            self.cache.lock()
            
            for id in _active_devices:
                if id not in self.device_ports:
                    self.device_ports[id] = {}
                    
                if id not in self.port_id_ifname_map:
                    self.port_id_ifname_map[id] = {0: "lo"}

                if id not in self.connected_macs:
                    self.connected_macs[id] = {}

                _device = _active_devices[id]
                
                mac = _device["mac"]
                device = self.cache.getDevice(mac)
                device.setIP(_device["ip"])
                device.setType(_device["type"])
                device.setDetail("hardware", _device["hardware"], "string")
                self.cache.confirmDevice( device, lambda event: events.append(event) )
                            
            for id in list(self.devices.keys()):
                if id not in _active_devices:
                    del self.devices[id]
                    del self.device_ports[id]
                        
            self.cache.unlock()
            
        if global_timeout > call_timeout:
            global_timeout = call_timeout

        return [global_timeout, now]
                
    def _processVLANs(self, now, events, global_timeout, call_timeout):
        _vlan_json = self._get("resources/vlans")
        _vlans = json.loads(_vlan_json)["vlans"]
        
        _active_vlan_ids = []
        for _vlan in _vlans:
            _active_vlan_ids.append(_vlan["vlan_id"])
            self.vlan_id_map[_vlan["vlan_id"]] = _vlan["vlan_vlan"]
        
        for vlan_id in list(self.vlan_id_map.keys()):
            if vlan_id not in _active_vlan_ids:
                del self.vlan_id_map[vlan_id]

        if global_timeout > call_timeout:
            global_timeout = call_timeout

        return [global_timeout, now]
    
    def _processPorts(self, now, events, global_timeout, call_timeout):    
        _ports_json = self._get("ports?columns=device_id,ifIndex,ifName,ifInOctets,ifOutOctets,ifSpeed,ifDuplex")
        _ports = json.loads(_ports_json)["ports"]

        for _port in _ports:
            if _port["device_id"] not in self.devices:
                [global_timeout, self.last_check["device"]] = self._processDevices(now, events, global_timeout, self.config.librenms_device_interval)
                for __port in _ports:
                    if __port["device_id"] not in self.devices:
                        raise Exception("Missing device {}".format(__port["device_id"]))
                break
            
        if _ports or self.device_ports:
            self.cache.lock()

            _active_ports_ids = []
            for _port in _ports:
                device_id = _port["device_id"]
                mac = self.devices[device_id]["mac"]
                port_ifname = _port["ifName"]
                port_id = _port["ifIndex"]
                
                self.port_id_ifname_map[device_id][port_id] = port_ifname
                
                #device = self.cache.getDevice(mac)
                #self.cache.confirmDevice( device, lambda event: events.append(event) )
                
                #if port_ifname in self.swapped_directions:
                #    assigned_devices = list(filter(lambda c: c["target_interface"] == port_ifname, self.connected_macs[device_id].values() ))
                #    if len(assigned_devices) == 1:
                #        mac = self.swapped_directions[port_ifname]
                #        port_ifname = None
                
                stat = self.cache.getConnectionStat(mac, port_ifname)
                if port_id in self.device_ports[device_id]:
                    time_diff = (now - self.device_ports[device_id][port_id]["refreshed"])
                    time_diff_slot = math.ceil(time_diff / self.config.librenms_poller_interval)
                    time_diff = time_diff_slot * self.config.librenms_poller_interval
                    
                    in_diff = _port["ifInOctets"] - stat.getInBytes()
                    if in_diff > 0 or time_diff > self.config.librenms_poller_interval * 2:
                        stat.setInAvg(in_diff / time_diff)

                    out_diff = _port["ifOutOctets"] - stat.getOutBytes()
                    if out_diff > 0 or time_diff > self.config.librenms_poller_interval * 2:
                        stat.setOutAvg(out_diff / time_diff)

                stat.setInBytes(_port["ifInOctets"])
                stat.setOutBytes(_port["ifOutOctets"])
                stat.setInSpeed(_port["ifSpeed"])
                stat.setOutSpeed(_port["ifSpeed"])
                stat.setDetail("duplex", "full" if _port["ifDuplex"] == "fullDuplex" else "half", "string")
                self.cache.confirmStat( stat, lambda event: events.append(event) )
                    
                _active_ports_ids.append("{}-{}".format(device_id, port_id))
                self.device_ports[device_id][port_id] = { "refreshed": now, "mac": mac, "interface": port_ifname }

            for device_id in self.device_ports:
                for port_id in list(self.device_ports[device_id].keys()):
                    if "{}-{}".format(device_id, port_id) not in _active_ports_ids:
                        _p = self.device_ports[device_id][port_id]
                        self.cache.removeConnectionStat(_p["mac"], _p["interface"], lambda event: events.append(event))
                        del self.device_ports[device_id][port_id]
                        del self.port_id_ifname_map[device_id][port_id]
                        
            self.cache.unlock()
            
        if global_timeout > call_timeout:
            global_timeout = call_timeout

        return [global_timeout, now]
    
    def _processFDP(self, now, events, global_timeout, call_timeout):        
        _connected_arps_json = self._get("resources/fdb")
        _connected_arps = json.loads(_connected_arps_json)["ports_fdb"]
        
        for _connected_arp in _connected_arps:
            if _connected_arp["vlan_id"] not in self.vlan_id_map:
                [timeout, self.last_check["vlan"]] = self._processVLANs(now, events, timeout, self.config.librenms_vlan_interval)
                for __connected_arp in _connected_arps:
                    if __connected_arp["vlan_id"] not in self.vlan_id_map:
                        raise Exception("Missing vlan {}".format(__connected_arp["vlan_id"]))
                break

        if _connected_arps or self.connected_macs:
            self.cache.lock()
            
            _active_connected_macs = []
            for _connected_arp in _connected_arps:
                vlan = self.vlan_id_map[_connected_arp["vlan_id"]]
                device_id = _connected_arp["device_id"]
                port_id = _connected_arp["port_id"]
                target_mac = self.devices[device_id]["mac"]
                target_interface = self.port_id_ifname_map[device_id][port_id]
                if target_interface == "lo":
                    continue
                
                _mac = _connected_arp["mac_address"]
                mac = ":".join([_mac[i:i+2] for i in range(0, len(_mac), 2)])
                
                if mac == self.cache.getGatewayMAC():
                    continue
                
                if self.cache.getUnlockedDevice(mac) is not None and self.cache.getUnlockedDevice(target_mac) is not None:
                    device = self.cache.getDevice(mac)
                    device.addHopConnection(Connection.ETHERNET, vlan, target_mac, target_interface );
                    self.cache.confirmDevice( device, lambda event: events.append(event) )
                    
                _active_connected_macs.append(mac)
                self.connected_macs[device_id][mac] = {"vlan": vlan, "source_mac": mac, "target_mac": target_mac, "target_interface": target_interface}

            for device_id in self.connected_macs:
                for mac in list(self.connected_macs[device_id].keys()):
                    if mac not in _active_connected_macs:
                        vlan = self.connected_macs[device_id][mac]["vlan"]
                        target_mac = self.connected_macs[device_id][mac]["target_mac"]
                        target_interface = self.connected_macs[device_id][mac]["target_interface"]
                        
                        device = self.cache.getDevice(mac)
                        device.removeHopConnection(vlan, target_mac, target_interface)
                        self.cache.confirmDevice( device, lambda event: events.append(event) )
                    
                        del self.connected_macs[device_id][mac]
            
            self.cache.unlock()
            
        if global_timeout > call_timeout:
            global_timeout = call_timeout

        return [global_timeout, now]
    
    def _get(self,call):
        headers = {'X-Auth-Token': self.config.librenms_token}
        
        #print("{}{}".format(self.config.librenms_rest,call))
        r = requests.get( "{}{}".format(self.config.librenms_rest,call), headers=headers)
        if r.status_code != 200:
            msg = "Wrong status code: {}".format(r.status_code)
            logging.error(msg)
            raise requests.exceptions.ConnectionError(msg)
        return r.text
    
    def getEventTypes(self):
        return [ { "types": [Event.TYPE_DEVICE], "actions": [Event.ACTION_CREATE], "details": None } ]

    def processEvents(self, events):
        _events = []
        
        for event in events:
            if event.getAction() == Event.ACTION_CREATE:
                mac =  event.getObject().getMAC()

                for device_macs in list(self.connected_macs.values()):
                    for cm in list(device_macs.values()):
                        if cm["source_mac"] != mac and cm["target_mac"] != mac:
                            continue
                            
                        if self.cache.getUnlockedDevice(cm["source_mac"]) is not None and self.cache.getUnlockedDevice(cm["target_mac"]) is not None:    
                            device = self.cache.getDevice(cm["source_mac"])
                            device.addHopConnection(Connection.ETHERNET, cm["vlan"], cm["target_mac"], cm["target_interface"] );
                            self.cache.confirmDevice( device, lambda event: _events.append(event) )
                            
            #elif event.getAction() != Event.ACTION_MODIFY:
            #    with self.data_lock:
            #        # fill fallback connections
            #        _connected_arps = list(filter(lambda a: a["source_mac"] == event.getIdentifier(), self.connected_arps.values() ))
            #        for _connected_arp in _connected_arps:
            #            self._fillConnection(_connected_arp, devices, True)

        if len(_events) > 0:
            self._getDispatcher().dispatch(self, _events)

class NetworkException(Exception):
    pass
