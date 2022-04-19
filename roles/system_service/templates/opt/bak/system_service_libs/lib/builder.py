from datetime import datetime, timedelta
import threading

from lib.dto.device import Device
from lib.dto.event import Event


class Builder(): 
    def __init__(self, logger, config, pipeline ):
        self.logger = logger
        self.config = config
        self.pipeline = pipeline
        
        self.groups = []
        self.devices = []
        self.stats = []

        self.hub_devices = []

        self.last_group_refresh = 0
        self.last_device_refresh = 0
        self.last_stats_refresh = 0

        self.data_lock = threading.Lock()
               
    def build(self, source_watcher, events):
        
        with self.data_lock:
            _event_names = []
            for event in events:
                _event_names.append(str(event))
            self.logger.info("Processed events: {} => {}".format(type(source_watcher).__name__, list(set(_event_names))))

            source_watcher.processEvents( self.groups, self.devices, self.stats, events )
            
            events = list(filter(lambda e: e.getAction() != Event.ACTION_SKIP, events ))

            group_changed = len(list(filter(lambda e: e.getType() == Event.TYPE_GROUP, events ))) > 0
            device_changed = len(list(filter(lambda e: e.getType() == Event.TYPE_DEVICE, events ))) > 0
            stats_changed = len(list(filter(lambda e: e.getType() in [Event.TYPE_DEVICE_STAT, Event.TYPE_PORT_STAT], events ))) > 0

            _event_names = []
            for event in events:
                _event_names.append(str(event))
            self.logger.info("Notified events: {} => {}".format(type(source_watcher).__name__, list(set(_event_names))))

            if device_changed:
                connected_map = {}
                for device in self.devices:
                    if device.getConnectionType() != Device.CONNECTION_TYPE_ETHERNET:
                        device.removeConnectionTarget(Device.CONNECTION_TYPE_VIRTUAL)
                        continue
                    
                    key = "{}-{}".format(device.getConnectionTargetUID(),device.getConnectionTargetPort())
                    #self.logger.info("uid: "+ device.getUID())
                    
                    if key not in connected_map:
                        connected_map[key] = []
                        #self.logger.info("new key: "+ key)
                        #self.logger.info("c-uid: "+ str(device.getConnectedToUId()))
                        #self.logger.info("c-port: "+ str(device.getConnectedToPort()))
                        
                    connected_map[key].append(device)
                    
                hub_devices = []
                # **** INSERT DUMMY HUBS ****
                for key in connected_map:
                    if len(connected_map[key]) == 1:
                        device.removeConnectionTarget(Device.CONNECTION_TYPE_VIRTUAL)
                        continue
                    
                    #self.logger.info("key: "+ key)
                    [target_uid, target_port] = key.split("-")
                    
                    device = Device(key,"hub")
                    device.setConnectionTarget( target_uid, target_port, device.getConnectionVLAN(), device.getConnectionType() );

                    i = 0
                    for connection_target_device in connected_map[key]:
                        connection_target_device.setConnectionTarget( device.getUID(), i, device.getConnectionVLAN(), Device.CONNECTION_TYPE_VIRTUAL );
                        i += 1
                        
                    hub_devices.append(device)
                    
                self.hub_devices = hub_devices

            for watcher in self.pipeline:
                if watcher == source_watcher:
                    continue

                watcher.triggerEvents( self.groups, self.devices, self.stats, events)
                
            if group_changed:
                self.last_group_refresh = round(datetime.now().timestamp(),3)

            if device_changed:
                self.last_device_refresh = round(datetime.now().timestamp(),3)
            
            if stats_changed:
                self.last_stats_refresh = round(datetime.now().timestamp(),3)
            
    def getGroups(self):
        _groups = []
        for group in self.groups:
            _groups.append(group.getSerializeable())
        return _groups

    def getLastGroupRefreshAsTimestamp(self):
        return self.last_group_refresh

    def getDevices(self):
        _devices = []
        for device in self.devices:
            _devices.append(device.getSerializeable())
        for device in self.hub_devices:
            _devices.append(device.getSerializeable())
        return _devices

    def getLastDeviceRefreshAsTimestamp(self):
        return self.last_device_refresh

    def getStats(self):
        stats = []
        for stat in self.stats:
            
            target = stat.getTarget()
            type = stat.getType()
            
            if type == "port":
                continue

                [ip, port] = target.split(":")
                target_devices = list(filter(lambda d: d.getIP() == ip, self.devices ))[0]
                # FIXME virtual devices
                source_devices = list(filter(lambda d: d.getConnectionType() == Device.CONNECTION_TYPE_ETHERNET and d.getConnectionTargetUID() == target_device.getMAC() and d.getConnectionTargetPort() == port, self.devices ))
            else:
                source_devices = list(filter(lambda d: d.getUID() == target, self.devices ))
            
            if len(source_devices) > 0:
                #print(stat.getSerializeable(source_devices[0].getUID()))
                
                stats.append(stat.getSerializeable(source_devices[0].getUID()))
        return stats

    def getLastStatsRefreshAsTimestamp(self):
        return self.last_stats_refresh
