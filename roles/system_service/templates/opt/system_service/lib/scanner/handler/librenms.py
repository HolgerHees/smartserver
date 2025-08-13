from datetime import datetime, timedelta
import re
import requests
import json
import math
import logging

from smartserver import command

from lib.scanner.handler import _handler
from lib.scanner.dto._changeable import Changeable
from lib.scanner.dto.device import Device, Connection
from lib.scanner.dto.event import Event
from lib.scanner.helper import Helper


class LibreNMS(_handler.Handler): 
    DEFAULT_VLAN_ID = 0
    DEFAULT_VLAN_VLAN = 1


    def __init__(self, config, cache ):
        super().__init__(config,cache)
        
        self.next_run = {}
        
        self.devices = {}
        
        self.device_ports = {}
        self.vlan_id_map = {}
        self.port_id_ifname_map = {}
        self.connected_macs = {}
        
        # use request session for keepalive support of librenms
        self.request_session = requests.Session()

        self._setServiceMetricState("librenms", -1)

    def _initNextRuns(self):
        now = datetime.now()
        self.next_run = {"device": now, "vlan": now, "port": now, "fdb": now}
                    
    def _run(self):
        self._initNextRuns()

        while self._isRunning():
            if not self._isSuspended():
                try:
                    self._processLibreNMS()
                    self._setServiceMetricState("librenms", 1)
                except NetworkException as e:
                    self._initNextRuns()
                    self.cache.cleanLocks(self)

                    self._handleExpectedException(str(e), None, e.getTimeout())
                    self._setServiceMetricState("librenms", 0)
                except Exception as e:
                    self._initNextRuns()
                    self.cache.cleanLocks(self)

                    self._handleUnexpectedException(e)
                    self._setServiceMetricState("librenms", -1)

            suspend_timeout = self._getSuspendTimeout()
            if suspend_timeout > 0:
                timeout = suspend_timeout
            else:
                timeout = 9999999999
                now = datetime.now()
                for next_run in self.next_run.values():
                    diff = (next_run - now).total_seconds()
                    if diff < timeout:
                        timeout = diff
                    
            if timeout > 0:
                self._wait(timeout)
                    
    def _processLibreNMS(self):
        if self.next_run["device"] <= datetime.now():
            self._processDevices()
                                        
        if self.next_run["vlan"] <= datetime.now():
            self._processVLANs()

        if self.next_run["port"] <= datetime.now():
            self._processPorts()
    
        if self.next_run["fdb"] <= datetime.now():               
            self._processFDP()

    def _processDevices(self):
        self.next_run["device"] = datetime.now() + timedelta(seconds=self.config.librenms_device_interval)
        
        start = datetime.now()
        _device_json = self._get("api/v0/devices")
        Helper.logProfiler(self, start, "Devices fetched")
        
        _devices = _device_json["devices"]
        
        _active_devices = {}
        for _device in _devices:
            mac = self.cache.ip2mac(_device["hostname"],self._isRunning)
            if mac is None:
                if _device["device_id"] in self.devices:
                    mac = self.devices[_device["device_id"]]["mac"]
                    logging.info("Device {} currently not resolvable. Use old mac address for now.".format(_device["hostname"]))
                else:
                    logging.info("Device {} currently not resolvable. Skip for now.".format(_device["hostname"]))
                    continue
                    #raise NetworkException("Device {} currently not resolvable".format(_device["hostname"]), self.config.startup_error_timeout)
            
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
                self.cache.confirmDevice( self, device )
                            
            for id in list(self.devices.keys()):
                if id not in _active_devices:
                    device = self.cache.getUnlockedDevice(self.devices[id]["mac"])
                    if device is not None:
                        device.lock(self)
                        device.removeType("librenms")
                        device.removeIP("librenms")
                        device.removeDetail("hardware")
                        self.cache.confirmDevice( self, device )
                    
                    del self.devices[id]
                    del self.device_ports[id]
                        
            self.cache.unlock(self)
                
    def _processVLANs(self):
        self.next_run["vlan"] = datetime.now() + timedelta(seconds=self.config.librenms_vlan_interval)

        start = datetime.now()
        _vlan_json = self._get("api/v0/resources/vlans", { 404: { 'vlans': [ {'vlan_id': LibreNMS.DEFAULT_VLAN_ID, 'vlan_vlan': LibreNMS.DEFAULT_VLAN_VLAN} ] } })
        Helper.logProfiler(self, start, "VLANs fetched")

        _vlans = _vlan_json["vlans"]

        _active_vlan_ids = []
        for _vlan in _vlans:
            _active_vlan_ids.append(_vlan["vlan_id"])
            self.vlan_id_map[_vlan["vlan_id"]] = _vlan["vlan_vlan"]
        
        for vlan_id in list(self.vlan_id_map.keys()):
            if vlan_id not in _active_vlan_ids:
                del self.vlan_id_map[vlan_id]
    
    def _processPorts(self):
        self.next_run["port"] = datetime.now() + timedelta(seconds=self.config.librenms_port_interval)

        start = datetime.now()
        _ports_json = self._get("api/v0/ports?columns=device_id,port_id,ifIndex,ifName,ifInOctets,ifOutOctets,ifSpeed,ifDuplex")
        Helper.logProfiler(self, start, "Ports fetched")

        _ports = _ports_json["ports"]

        for _port in _ports:
            if _port["device_id"] not in self.devices:
                self._processDevices()
                #for __port in _ports:
                #    if __port["device_id"] not in self.devices:
                #        logging.warning("Device {} currently not resolvable. Skip for now.".format(_device["hostname"]))
                #        #raise Exception("Missing device {}".format(__port["device_id"]))
                break
            
        if _ports or self.device_ports:
            self.cache.lock(self)

            now = datetime.now()

            _active_ports_ids = []
            for _port in _ports:
                device_id = _port["device_id"]
                if device_id not in self.devices:
                  continue
                mac = self.devices[device_id]["mac"]
                port_ifname = _port["ifName"]
                #port_id = _port["ifIndex"]
                port_id = _port["port_id"]
                
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
                self.cache.confirmStat( self, stat )
                    
                _active_ports_ids.append("{}-{}".format(device_id, port_id))
                self.device_ports[device_id][port_id] = { "refreshed": now, "mac": mac, "interface": port_ifname }

            for device_id in self.device_ports:
                for port_id in list(self.device_ports[device_id].keys()):
                    if "{}-{}".format(device_id, port_id) not in _active_ports_ids:
                        _p = self.device_ports[device_id][port_id]
                        self.cache.removeConnectionStat(self, _p["mac"], _p["interface"])
                        del self.device_ports[device_id][port_id]
                        del self.port_id_ifname_map[device_id][port_id]
                        
            self.cache.unlock(self)
    
    def _processFDP(self):
        self.next_run["fdb"] = datetime.now() + timedelta(seconds=self.config.librenms_fdb_interval)

        start = datetime.now()

        uplinks = {}
        _uplink_json = self._get("custom/stp")
        for stp in _uplink_json['stp']:
            if stp['uplink_mac'] == '00:00:00:00:00:00':
                stp['uplink_mac'] = self.cache.getGatewayMAC()
            uplinks[self.devices[stp['device_id']]['mac']] = stp['uplink_mac']

        _connected_arps_json = self._get("api/v0/resources/fdb")
        Helper.logProfiler(self, start, "Clients fetched")

        _connected_arps = _connected_arps_json["ports_fdb"]
        
        if _connected_arps or self.connected_macs:
            self.cache.lock(self)
            
            _active_connected_macs = []
            for _connected_arp in _connected_arps:
                device_id = _connected_arp["device_id"]
                if device_id not in self.devices:
                  continue

                port_id = _connected_arp["port_id"]
                if port_id not in self.port_id_ifname_map[device_id]:
                    logging.info("Skip unknown/deprecated port {} of device {}".format(port_id, device_id))
                    continue

                if "vlan_id" not in _connected_arp:
                    vlan = LibreNMS.DEFAULT_VLAN_VLAN
                    logging.info("Fallback for missing vlan of device {}".format(device_id))
                elif _connected_arp["vlan_id"] not in self.vlan_id_map:
                    vlan = LibreNMS.DEFAULT_VLAN_VLAN
                    #logging.info("Fallback for unknown/deprecated vlan of device {}".format(device_id))
                    #logging.info("Skip unknown/deprecated vlan {} of device {}".format(_connected_arp["vlan_id"], device_id))
                else:
                    vlan = self.vlan_id_map[_connected_arp["vlan_id"]]

                target_mac = self.devices[device_id]["mac"]
                target_interface = self.port_id_ifname_map[device_id][port_id]
                if target_interface == "lo":
                    continue

                _mac = _connected_arp["mac_address"]
                mac = ":".join([_mac[i:i+2] for i in range(0, len(_mac), 2)])
                if mac not in uplinks or target_mac == uplinks[mac]:
                    device = self.cache.getUnlockedDevice(mac)
                    if device is not None:
                        device.lock(self)
                        device.addHopConnection(Connection.ETHERNET, target_mac, target_interface, { "vlan": vlan } );
                        self.cache.confirmDevice( self, device )

                    _active_connected_macs.append(mac)
                    self.connected_macs[device_id][mac] = { "source_mac": mac, "target_mac": target_mac, "target_interface": target_interface, "details": { "vlan": vlan } }

            for device_id in self.connected_macs:
                for mac in list(self.connected_macs[device_id].keys()):
                    if mac not in _active_connected_macs:
                        device = self.cache.getUnlockedDevice(mac)
                        if device is not None:
                            details = self.connected_macs[device_id][mac]["details"]
                            target_mac = self.connected_macs[device_id][mac]["target_mac"]
                            target_interface = self.connected_macs[device_id][mac]["target_interface"]

                            device.lock(self)
                            device.removeHopConnection(Connection.ETHERNET, target_mac, target_interface, details)
                            self.cache.confirmDevice( self, device )
                    
                        del self.connected_macs[device_id][mac]
            
            self.cache.unlock(self)
            
    def _isInitialized(self):
        return len(self.devices.values()) > 0
    
    def _get(self, call, additional_codes = {} ):
        headers = {'X-Auth-Token': self.config.librenms_token}

        try:
            #print("{}{}".format(self.config.librenms_rest,call))
            r = self.request_session.get( "{}{}".format(self.config.librenms_rest,call), headers=headers)
            if r.status_code != 200:
                if r.status_code in additional_codes:
                    return additional_codes[r.status_code]
                raise NetworkException("Got wrong response status code: {}".format(r.status_code), self.config.startup_error_timeout if not self._isInitialized() else self.config.remote_suspend_timeout)

            data = json.loads(r.text)
            if data["status"] != "ok":
                raise NetworkException("Got wrong data status code: {}".format(data["status"]), self.config.startup_error_timeout if not self._isInitialized() else self.config.remote_suspend_timeout)

            return data
        except json.decoder.JSONDecodeError as e:
            logging.error("{} {}".format(r.status_code, r.text))
            raise NetworkException("LibreNMS result was unparseable", self.config.remote_suspend_timeout )
        except requests.exceptions.ConnectionError as e:
            #logging.error(str(e))
            raise NetworkException("LibreNMS currently not available", self.config.startup_error_timeout if not self._isInitialized() else self.config.remote_suspend_timeout )
    
    def getEventTypes(self):
        return [ { "types": [Event.TYPE_DEVICE], "actions": [Event.ACTION_CREATE], "details": None } ]

    def processEvents(self, events):
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
                self.cache.confirmDevice( self, device )
            self.cache.unlock(self)

class NetworkException(Exception):
    def __init__(self, msg, timeout):
        super().__init__(msg)
        
        self.timeout = timeout
        
    def getTimeout(self):
        return self.timeout
