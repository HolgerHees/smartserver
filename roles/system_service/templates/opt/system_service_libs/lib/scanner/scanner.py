from datetime import datetime, timedelta
import threading
import logging
from collections import deque
import traceback

from lib.scanner.dto.device import Device, Connection
from lib.scanner.dto.event import Event

from lib.scanner.cache import Cache

from lib.scanner.handler.arpscan import ArpScanner

from lib.scanner.handler.openwrt import OpenWRT
from lib.scanner.handler.librenms import LibreNMS
from lib.scanner.handler.fritzbox import Fritzbox
from lib.scanner.handler.portscan import PortScanner
from lib.scanner.handler.gateway import Gateway

from lib.scanner.handler.publish_mqtt import MQTTPublisher
from lib.scanner.handler.publish_influxdb import InfluxDBPublisher

class Scanner(threading.Thread):
    def __init__(self, config, handler, mqtt, influxdb ):
        threading.Thread.__init__(self)

        self.is_running = True
        self.is_initialized = False
        
        self.config = config
        self.handler = handler
        
        self.event_pipeline = []
        self.registered_handler = []

        self.virtual_devices = []
        
        self.event_queue = deque()
        
        self.event = threading.Event()
        #self.thread = threading.Thread(target=self._worker, args=())
        
        self.cache = Cache(config)

        self._register(ArpScanner(config, self.cache ))
        if len(config.openwrt_devices) > 0:
            self._register(OpenWRT(config, self.cache ))
        if len(config.fritzbox_devices) > 0:
            self._register(Fritzbox(config, self.cache ))
        if config.librenms_token:
            self._register(LibreNMS(config, self.cache ))
        self._register(PortScanner(config, self.cache ))
        self._register(Gateway(config, self.cache ))
        self._register(MQTTPublisher(config, self.cache, mqtt ))
        self._register(InfluxDBPublisher(config, self.cache, influxdb ))

    def _register(self, handler):
        handler.setDispatcher(self)

        self.registered_handler.append(handler)
        
        event_types = handler.getEventTypes()
        if len(event_types) == 0:
            return
        
        self.event_pipeline.append([event_types, handler])
        
    #def start(self):
    #    self.thread.start()
        
    def terminate(self):
        self.is_running = False
        self.event.set()
        
        for handler in self.registered_handler:
            handler.terminate()
               
    def dispatch(self, source_handler, events):
        self.event_queue.append([source_handler,events])
        self.event.set()
            
    def run(self):
        for handler in self.registered_handler:
            handler.start()

        try:
            while self.is_running:
                while len(self.event_queue) > 0:
                    [source_handler,events] = self.event_queue.popleft()
                    self._dispatch(source_handler, events)
                self.event.wait()
                self.event.clear()
        except Exception:
            logging.error(traceback.format_exc())
            self.is_running = False


    #def dispatch(self, source_handler, events):
    def _dispatch(self, source_handler, events):
        # *** recalculate main connection ***
        has_connection_changes = False
        for event in events:
            #logging.info("DEBUG: {} {}".format(str(source_handler.__class__),event))
            if event.getType() == Event.TYPE_DEVICE and event.hasDetail("connection"):
                has_connection_changes = True
                break
        
        if has_connection_changes:
            has_connection_changes = False
            self.cache.lock(self)
            #for device in self.cache.getDevices():   
            #    device.resetConnection()
            processed_devices = {}    
            unprocessed_devices = []
            for device in self.cache.getDevices():   
                if device.calculateConnectionPath(processed_devices):
                    has_connection_changes = True
                else:
                    unprocessed_devices.append(device)

            # cleanup
            for event in list(events):
                if event.getObject() in unprocessed_devices:
                    if event.hasDetail("connection_helper"):
                        #logging.info(">>>>>>>>>>>>>> CLEAN")
                        events.remove(event)
                    
            self.cache.unlock(self)
            
            if len(events) == 0:
                #logging.info(">>>>>>>>>>>>>> SKIP")
                return
        # ***********************************
        
        for [event_types, handler] in self.event_pipeline:
            if handler == source_handler:
                continue
            
            _events = []
            for event_type in event_types:
                for event in events:
                    if event_type["types"] is not None and event.getType() not in event_type["types"]:
                        continue
                    if event_type["actions"] is not None and event.getAction() not in event_type["actions"]:
                        continue
                    if event_type["details"] is not None:
                        found = False
                        for detail in event_type["details"]:
                            if event.hasDetail(detail):
                                found = True
                                break
                        if not found:
                            continue
                    _events.append(event)
                
            if len(_events) > 0:
                handler.processEvents(_events)
                               
        if has_connection_changes:
            connected_map = {}
            for device in self.cache.getDevices():               
                device.setVirtualConnection(None)
                connection = device.getConnection()
                if connection is None or connection.getType() != Connection.ETHERNET:
                    continue
                
                key = "{}-{}".format(connection.getTargetMAC(),connection.getTargetInterface())
                if key not in connected_map:
                    connected_map[key] = []
                connected_map[key].append( device )
                
            # **** INSERT DUMMY HUBS ****
            virtual_devices = []
            for key in connected_map:
                if len(connected_map[key]) == 1:
                    continue
                
                _device = connected_map[key][0]
                _connection = _device.getConnection()
                details_list = _connection.getDetailsList()
                target_mac = _connection.getTargetMAC()
                target_interface = _connection.getTargetInterface()
                
                #logging.info("{} {}".format(key, len(connected_map[key])))
                #for device in connected_map[key]:
                #    logging.info("  - {}".format(device.getMAC()))
                
                virtual_device = Device(self.cache, key,"hub")
                virtual_connection = Connection(Connection.ETHERNET, target_mac, target_interface, details_list)
                virtual_device.setVirtualConnection(virtual_connection)
                
                for device in connected_map[key]:
                    virtual_connection = Connection(Connection.VIRTUAL, virtual_device.getMAC(), "hub", details_list)
                    device.setVirtualConnection(virtual_connection)
                    
                virtual_devices.append(virtual_device)
                
            self.virtual_devices = virtual_devices
            
        [ changed_data, msg ] = self._convertEvents(events, has_connection_changes)

        self.handler.notifyNetworkData(changed_data, msg)

    def _convertEvents(self, events, has_connection_changes):
        full_device_update_needed = has_connection_changes
        devices_added = []
        devices_modified = []
        devices_deleted = []

        groups_added = []
        groups_modified = []
        groups_deleted = []

        stats_added = []
        stats_modified = []
        stats_deleted = []

        for event in events:
            if event.getType() == Event.TYPE_DEVICE:
                if event.getAction() == Event.ACTION_CREATE:
                    devices_added.append(event.getObject())
                elif event.getAction() == Event.ACTION_DELETE:
                    devices_deleted.append(event.getObject())
                else:
                    devices_modified.append(event.getObject())
            elif event.getType() == Event.TYPE_GROUP:
                if event.getAction() == Event.ACTION_CREATE:
                    groups_added.append(event.getObject())
                elif event.getAction() == Event.ACTION_DELETE:
                    groups_deleted.append(event.getObject())
                else:
                    groups_modified.append(event.getObject())
            elif event.getType() == Event.TYPE_DEVICE_STAT or event.getType() == Event.TYPE_CONNECTION_STAT:
                if event.getAction() == Event.ACTION_CREATE:
                    stats_added.append(event.getObject())
                elif event.getAction() == Event.ACTION_DELETE:
                    stats_deleted.append(event.getObject())
                else:
                    stats_modified.append(event.getObject())
                    
        all_devices = self.cache.getDevices() + self.virtual_devices
        #if full_device_update_needed:
        #    devices_modified = all_devices
            
        return self._prepareChanges( devices_added, devices_modified, devices_deleted, has_connection_changes, all_devices, groups_added, groups_modified, groups_deleted, stats_added, stats_modified, stats_deleted )

    def _prepareChanges(self, devices_added, devices_modified, devices_deleted, has_connection_changes, all_devices, groups_added, groups_modified, groups_deleted, stats_added, stats_modified, stats_deleted ):
        msg = "devices: [{},{},{}] - groups: [{},{},{}] - stats: [{},{},{}] ".format(len(devices_added), len(devices_modified), len(devices_deleted), len(groups_added), len(groups_modified), len(groups_deleted), len(stats_added), len(stats_modified), len(stats_deleted))

        changed_data = {}
        
        changed_data["devices"] = { "values": [], "replace": False }
        if has_connection_changes or devices_added or devices_deleted:
            changed_data["devices"]["replace"] = True
            for device in all_devices:
                changed_data["devices"]["values"].append(device.getSerializeable(all_devices))
        else:
            #for device in devices_added:
            #    changed_data["devices"]["added"].append(device.getSerializeable(all_devices))
            for device in devices_modified:
                changed_data["devices"]["values"].append(device.getSerializeable(all_devices))
            #for device in devices_deleted:
            #    changed_data["devices"]["deleted"].append(device.getSerializeable(all_devices))

        changed_data["groups"] = { "added": [], "modified": [], "deleted": [] }
        for group in groups_added:
            changed_data["groups"]["added"].append(group.getSerializeable())
        for group in groups_modified:
            changed_data["groups"]["modified"].append(group.getSerializeable())
        for group in groups_deleted:
            changed_data["groups"]["deleted"].append(group.getSerializeable())
            
        changed_data["stats"] = { "added": [], "modified": [], "deleted": [] }
        for stat in stats_added:
            changed_data["stats"]["added"].append(stat.getSerializeable())
        for stat in stats_modified:
            changed_data["stats"]["modified"].append(stat.getSerializeable())
        for stat in stats_deleted:
            changed_data["stats"]["deleted"].append(stat.getSerializeable())

        return [ changed_data, msg ]
    
    def getWebSocketData(self):
        devices = self.cache.getDevices() + self.virtual_devices
        return self._prepareChanges(devices, [], [], False, devices, self.cache.getGroups(), [], [], self.cache.getStats(), [], [])

    def getGatewayMAC(self):
        return self.cache.getGatewayMAC()

    def getStateMetrics(self):
        metrics = []
        for handler in self.registered_handler:
            metrics += handler.getStateMetrics()
        metrics.append("system_service_process{{type=\"scanner\",}} {}".format("1" if self.is_running else "0"))
        return metrics
