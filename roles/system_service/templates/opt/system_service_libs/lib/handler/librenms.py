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
        
        self.next_run = {}
        
        self.devices = {}
        
        self.device_ports = {}
        self.vlan_id_map = {}
        self.port_id_ifname_map = {}
        self.connected_macs = {}
        
        # use request session for keepalive support of librenms
        self.request_session = requests.Session()

    def _run(self):
        now = datetime.now()
        self.next_run = {"device": now, "vlan": now, "port": now, "fdb": now}
        
        while self._isRunning():
            #RequestHeader set "X-Auth-Token" "{{vault_librenms_api_token}}"
            
            events = []
            
            timeout = 9999999999
            
            try:
                if self._isSuspended():
                    self._confirmSuspended()
                
                self._processLibreNMS(events)
            except NetworkException as e:
                logging.warning("{}. Will retry in {} seconds.".format(str(e), e.getTimeout()))
                timeout = e.getTimeout()
                self._suspend()
            except Exception as e:
                self.cache.cleanLocks(self, events)
                timeout = self._handleUnexpectedException(e)
                    
            if len(events) > 0:
                self._getDispatcher().dispatch(self,events)
                
            now = datetime.now()
            for next_run in self.next_run.values():
                diff = (next_run - now).total_seconds()
                if diff < timeout:
                    timeout = diff

            if timeout > 0:
                if self._isSuspended():
                    self._sleep(timeout)
                else:
                    self._wait(timeout)
                    
    def _processLibreNMS(self, events):
        if self.next_run["device"] <= datetime.now():
            self._processDevices(events)
                                        
        if self.next_run["vlan"] <= datetime.now():
            self._processVLANs(events)

        if self.next_run["port"] <= datetime.now():
            self._processPorts(events)
    
        if self.next_run["fdb"] <= datetime.now():               
            self._processFDP(events)

    def _processDevices(self, events):
        self.next_run["device"] = datetime.now() + timedelta(seconds=self.config.librenms_device_interval)
        
        start = datetime.now()
        _device_json = self._get("devices")
        Helper.logProfiler(self, start, "Devices fetched")
        
        _devices = json.loads(_device_json)["devices"]
        
        _active_devices = {}
        for _device in _devices:
            mac = self.cache.ip2mac(_device["hostname"])
            if mac is None:
                if device["id"] in self.devices:
                    mac = self.devices[device["id"]]["mac"]
                    logging.warning("Device {} currently not resolvable. User old mac address for now.".format(_device["hostname"]))
                else:
                    raise NetworkException("Device {} currently not resolvable".format(_device["hostname"]), 15)
            
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
            self.cache.lock(self)
            
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
                device.setType("librenms", 50, _device["type"])
                device.setIP("librenms", 50, _device["ip"])
                device.setDetail("hardware", _device["hardware"], "string")
                self.cache.confirmDevice( device, lambda event: events.append(event) )
                            
            for id in list(self.devices.keys()):
                if id not in _active_devices:
                    device = self.cache.getUnlockedDevice(self.devices[id]["mac"])
                    if device is not None:
                        device.lock(self)
                        device.removeType("librenms")
                        device.removeIP("librenms")
                        device.removeDetail("hardware")
                        self.cache.confirmDevice( device, lambda event: events.append(event) )
                    
                    del self.devices[id]
                    del self.device_ports[id]
                        
            self.cache.unlock(self)
                
    def _processVLANs(self, events):
        self.next_run["vlan"] = datetime.now() + timedelta(seconds=self.config.librenms_vlan_interval)

        start = datetime.now()
        _vlan_json = self._get("resources/vlans")
        Helper.logProfiler(self, start, "VLANs fetched")

        _vlans = json.loads(_vlan_json)["vlans"]
        
        _active_vlan_ids = []
        for _vlan in _vlans:
            _active_vlan_ids.append(_vlan["vlan_id"])
            self.vlan_id_map[_vlan["vlan_id"]] = _vlan["vlan_vlan"]
        
        for vlan_id in list(self.vlan_id_map.keys()):
            if vlan_id not in _active_vlan_ids:
                del self.vlan_id_map[vlan_id]
    
    def _processPorts(self, events):    
        self.next_run["port"] = datetime.now() + timedelta(seconds=self.config.librenms_port_interval)

        start = datetime.now()
        _ports_json = self._get("ports?columns=device_id,ifIndex,ifName,ifInOctets,ifOutOctets,ifSpeed,ifDuplex")
        Helper.logProfiler(self, start, "Ports fetched")

        _ports = json.loads(_ports_json)["ports"]

        for _port in _ports:
            if _port["device_id"] not in self.devices:
                self._processDevices(events)
                for __port in _ports:
                    if __port["device_id"] not in self.devices:
                        raise Exception("Missing device {}".format(__port["device_id"]))
                break
            
        if _ports or self.device_ports:
            self.cache.lock(self)

            now = datetime.now()

            _active_ports_ids = []
            for _port in _ports:
                device_id = _port["device_id"]
                mac = self.devices[device_id]["mac"]
                port_ifname = _port["ifName"]
                port_id = _port["ifIndex"]
                
                self.port_id_ifname_map[device_id][port_id] = port_ifname
                
                stat = self.cache.getConnectionStat(mac, port_ifname)
                stat_data = stat.getData()
                if port_id in self.device_ports[device_id]:
                    time_diff = (now - self.device_ports[device_id][port_id]["refreshed"]).total_seconds()
                    time_diff_slot = math.ceil(time_diff / self.config.librenms_poller_interval)
                    time_diff = time_diff_slot * self.config.librenms_poller_interval
                    
                    in_bytes = stat_data.getInBytes()
                    if in_bytes is not None:
                        in_diff = _port["ifInOctets"] - in_bytes
                        if in_diff > 0 or time_diff > self.config.librenms_poller_interval * 2:
                            stat_data.setInAvg(in_diff / time_diff)

                    out_bytes = stat_data.getOutBytes()
                    if out_bytes is not None:
                        out_diff = _port["ifOutOctets"] - out_bytes
                        if out_diff > 0 or time_diff > self.config.librenms_poller_interval * 2:
                            stat_data.setOutAvg(out_diff / time_diff)

                stat_data.setInBytes(_port["ifInOctets"])
                stat_data.setOutBytes(_port["ifOutOctets"])
                stat_data.setInSpeed(_port["ifSpeed"])
                stat_data.setOutSpeed(_port["ifSpeed"])
                stat_data.setDetail("duplex", "full" if _port["ifDuplex"] == "fullDuplex" else "half", "string")
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
                        
            self.cache.unlock(self)
    
    def _processFDP(self, events):        
        self.next_run["fdb"] = datetime.now() + timedelta(seconds=self.config.librenms_fdb_interval)

        start = datetime.now()
        _connected_arps_json = self._get("resources/fdb")
        Helper.logProfiler(self, start, "Clients fetched")

        _connected_arps = json.loads(_connected_arps_json)["ports_fdb"]
        
        for _connected_arp in _connected_arps:
            if _connected_arp["vlan_id"] not in self.vlan_id_map:
                self._processVLANs(events)
                for __connected_arp in _connected_arps:
                    if __connected_arp["vlan_id"] not in self.vlan_id_map:
                        raise Exception("Missing vlan {}".format(__connected_arp["vlan_id"]))
                break

        if _connected_arps or self.connected_macs:
            self.cache.lock(self)
            
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
                
                device = self.cache.getUnlockedDevice(mac)
                if device is not None:
                    device.lock(self)
                    device.addHopConnection(Connection.ETHERNET, target_mac, target_interface, { "vlan": vlan } );
                    self.cache.confirmDevice( device, lambda event: events.append(event) )
                
                _active_connected_macs.append(mac)
                self.connected_macs[device_id][mac] = { "source_mac": mac, "target_mac": target_mac, "target_interface": target_interface, "details": { "vlan": vlan } }

            for device_id in self.connected_macs:
                for mac in list(self.connected_macs[device_id].keys()):
                    if mac not in _active_connected_macs:
                        details = self.connected_macs[device_id][mac]["details"]
                        target_mac = self.connected_macs[device_id][mac]["target_mac"]
                        target_interface = self.connected_macs[device_id][mac]["target_interface"]
                        
                        device = self.cache.getDevice(mac)
                        device.removeHopConnection(Connection.ETHERNET, target_mac, target_interface, details)
                        self.cache.confirmDevice( device, lambda event: events.append(event) )
                    
                        del self.connected_macs[device_id][mac]
            
            self.cache.unlock(self)
    
    def _get(self,call):
        headers = {'X-Auth-Token': self.config.librenms_token}
        
        try:
            #print("{}{}".format(self.config.librenms_rest,call))
            r = self.request_session.get( "{}{}".format(self.config.librenms_rest,call), headers=headers)
            if r.status_code != 200:
                raise NetworkException("Got wrong status code: {}".format(r.status_code), self.config.remote_suspend_timeout)
            return r.text
        except requests.exceptions.ConnectionError as e:
            logging.error(str(e))
            raise NetworkException("LibreNMS currently not available", self.config.remote_suspend_timeout)
    
    def getEventTypes(self):
        return [ { "types": [Event.TYPE_DEVICE], "actions": [Event.ACTION_CREATE], "details": None } ]

    def processEvents(self, events):
        _events = []
        
        unprocessed_connections = []
        for event in events:
            if event.getAction() == Event.ACTION_CREATE:
                mac =  event.getObject().getMAC()

                for device_macs in list(self.connected_macs.values()):
                    if mac not in list(device_macs.keys()):
                        continue
                    
                    unprocessed_connections.append(device_macs[mac])

        if len(unprocessed_connections) > 0:
            self.cache.lock(self)
            for connection_data in unprocessed_connections:
                device = self.cache.getDevice(connection_data["source_mac"])
                device.addHopConnection(Connection.ETHERNET, connection_data["target_mac"], connection_data["target_interface"], connection_data["details"] );
                self.cache.confirmDevice( device, lambda event: _events.append(event) )
            self.cache.unlock(self)
            
        if len(_events) > 0:
            self._getDispatcher().dispatch(self, _events)

class NetworkException(Exception):
    def __init__(self, msg, timeout):
        super().__init__(msg)
        
        self.timeout = timeout
        
    def getTimeout(self):
        return self.timeout
