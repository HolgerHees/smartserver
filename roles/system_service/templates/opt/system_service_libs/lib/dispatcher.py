from datetime import datetime, timedelta
import threading
import logging


from lib.dto.device import Device, Connection
from lib.dto.event import Event


class Dispatcher(): 
    def __init__(self, config, cache, handler ):
        self.config = config
        self.cache = cache
        self.handler = handler
        
        self.event_pipeline = []
        self.registered_handler = []

        self.virtual_devices = []
        
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
        has_connection_changes = False
        for event in events:
            if event.getType() == Event.TYPE_DEVICE and event.hasDetail("connection"):
                has_connection_changes = True
                break
        
        if has_connection_changes:
            self.cache.lock(self)
            for device in self.cache.getDevices():   
                device.resetConnection()
                
            processed_devices = {}    
            for device in self.cache.getDevices():   
                device.calculateConnectionPath(processed_devices)
            self.cache.unlock(self)
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
            elif event.getType() == Event.TYPE_STAT:
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
    
    def getData(self):
        devices = self.cache.getDevices() + self.virtual_devices
        return self._prepareChanges(devices, [], [], False, devices, self.cache.getGroups(), [], [], self.cache.getStats(), [], [])
