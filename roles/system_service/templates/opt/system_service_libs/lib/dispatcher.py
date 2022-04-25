from datetime import datetime, timedelta
import threading
import logging


from lib.dto.device import Device, Connection
from lib.dto.event import Event


class Dispatcher(): 
    def __init__(self, config, cache ):
        self.config = config
        self.cache = cache
        
        self.event_pipeline = []
        self.registered_handler = []

        self.virtual_devices = []

        self.last_group_refresh = 0
        self.last_device_refresh = 0
        self.last_stat_refresh = 0

        self.data_lock = threading.Lock()
        
    def register(self, handler):
        handler.setDispatcher(self)

        self.registered_handler.append(handler)
        
        event_types = handler.getEventTypes()
        if len(event_types) == 0:
            return
        
        self.event_pipeline.append([event_types, handler])
        
    def start(self):
        for handler in self.registered_handler:
            handler.start()
            
    def terminate(self):
        for handler in self.registered_handler:
            handler.terminate()
               
    def dispatch(self, source_handler, events):
        # *** recalculate main connection ***
        has_connections = False
        for event in events:
            if event.getType() == Event.TYPE_DEVICE and event.hasDetail("connection"):
                has_connections = True
                break
        
        if has_connections:
            for device in self.cache.getDevices():   
                device.resetConnection()
                
            processed_devices = {}    
            for device in self.cache.getDevices():   
                device.calculateConnectionPath(processed_devices)
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
                
        groups_changed = []
        devices_changed = []
        stats_changed = []
        for event in events:
            if event.getType() == Event.TYPE_GROUP:
                groups_changed.append(event.getObject())
            elif event.getType() == Event.TYPE_DEVICE:
                devices_changed.append(event.getObject())
            elif event.getType() == Event.TYPE_STAT:
                stats_changed.append(event.getObject())
                
        if len(devices_changed) > 0:
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
                _connections = _device.getHopConnections()
                vlans = _connections[0].getVLANs()
                target_mac = _connections[0].getTargetMAC()
                target_interface = _connections[0].getTargetInterface()
                
                #logging.info("{} {}".format(key, len(connected_map[key])))
                #for device in connected_map[key]:
                #    logging.info("  - {}".format(device.getMAC()))
                
                virtual_device = Device(self.cache, key,"hub")
                virtual_connection = Connection(Connection.ETHERNET, vlans[0], target_mac, target_interface)
                for i in range(1,len(vlans)):
                    virtual_connection.addVLAN(vlans[i])
                virtual_device.setVirtualConnection(virtual_connection)
                
                for device in connected_map[key]:
                    virtual_connection = Connection(Connection.VIRTUAL, vlans[0], virtual_device.getMAC(), "hub")
                    for i in range(1,len(vlans)):
                        virtual_connection.addVLAN(vlans[i])
                    device.setVirtualConnection(virtual_connection)
                    
                virtual_devices.append(virtual_device)
                
            self.virtual_devices = virtual_devices
            
        if len(groups_changed) > 0:
            self.last_group_refresh = round(datetime.now().timestamp(),3)

        if len(devices_changed) > 0:
            self.last_device_refresh = round(datetime.now().timestamp(),3)
        
        if len(stats_changed) > 0:
            self.last_stat_refresh = round(datetime.now().timestamp(),3)
            
    def getGroups(self):
        _groups = []
        for group in self.cache.getGroups():
            _groups.append(group.getSerializeable())
        return _groups

    def getLastGroupRefreshAsTimestamp(self):
        return self.last_group_refresh

    def getDevices(self):
        devices = self.cache.getDevices() + self.virtual_devices
        _devices = []
        for device in devices:
            _devices.append(device.getSerializeable(devices))
        return _devices

    def getLastDeviceRefreshAsTimestamp(self):
        return self.last_device_refresh

    def getStats(self):
        _stats = []
        for stat in self.cache.getStats():
            _stats.append(stat.getSerializeable())
        return _stats

    def getLastStatRefreshAsTimestamp(self):
        return self.last_stat_refresh
