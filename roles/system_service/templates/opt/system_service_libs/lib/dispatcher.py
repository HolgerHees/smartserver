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
        self.registered_handler.append(handler)
        
        event_types = handler.getEventTypes()
        if len(event_types) == 0:
            return
        
        self.event_pipeline.append([event_types, handler])
            
        handler.setDispatcher(self)
        
    def start(self):
        for handler in self.registered_handler:
            handler.start()
            
    def terminate(self):
        for handler in self.registered_handler:
            handler.terminate()
               
    def dispatch(self, source_handler, events):
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
                groups_changed.append(event.getObject().getGID())
            elif event.getType() == Event.TYPE_DEVICE:
                devices_changed.append(event.getObject().getMAC())
            elif event.getType() == Event.TYPE_STAT:
                stats_changed.append(event.getObject().getID())
                
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
                
                virtual_device = Device(key,"hub", self.cache)
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
        devices = self.cache.getDevices() + self.virtual_devices
        
        stats = []
        for stat in self.cache.getStats():
            
            mac = stat.getMAC()
            interface = stat.getInterface()
            
            if interface:
                # for interface based stats, we use the device pointing to this interface
                source_devices = list(filter(lambda d: d.getConnection() and d.getConnection().getType() == Connection.ETHERNET and d.getConnection().getTargetMAC() == mac and d.getConnection().getTargetInterface() == interface, devices ))
            else:
                source_devices = list(filter(lambda d: d.getMAC() == mac, devices ))
            
            if len(source_devices) > 0:
                source_device = source_devices[0]
                source_mac = source_device.getMAC()
                # for hub devices, we duplicate the port statistic
                force_online = False
                if source_device.getType() == "hub":
                    all_children_online = True
                    for _child_device in list(filter(lambda d: d.getConnection() and d.getConnection().getTargetMAC() == source_mac, devices )):
                        _child_stat = self.cache.getUnlockedStat(_child_device.getMAC())
                        if not _child_stat.isOnline():
                            all_children_online = False
                        stats.append([stat.getSerializeable(_child_device.getMAC(), skip_traffic = True), _child_device.getMAC(), "hub"])
                    if all_children_online:
                        force_online = True
                        
                #print(source_mac)
                stats.append([stat.getSerializeable(source_mac, force_online = force_online), source_mac, stat.getInterface()])
                
        device_stats = []
        for device in devices:
            device_stat = {}

            _stats = list(filter(lambda s: s[1] == device.getMAC() and s[2] is None , stats ))
            if len(_stats) > 0:
                for key in _stats[0][0]:
                    if key in device_stats and not _stats[0][0][key]:
                        continue
                    device_stat[key] = _stats[0][0][key]
                
            if device.getConnection() is not None and device.getConnection().getTargetInterface() is not None:
                _stats = list(filter(lambda s: s[1] == device.getMAC() and s[2] == device.getConnection().getTargetInterface() , stats ))
                if len(_stats) > 0:
                    for key in _stats[0][0]:
                        if key in device_stat and (key == "offline_since" or not _stats[0][0][key]):
                            continue
                        device_stat[key] = _stats[0][0][key]
                        
            device_stats.append(device_stat)
                
        return device_stats

    def getLastStatRefreshAsTimestamp(self):
        return self.last_stat_refresh
