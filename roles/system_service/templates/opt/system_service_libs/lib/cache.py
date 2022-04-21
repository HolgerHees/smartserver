import threading
import inspect
from datetime import datetime
import logging

from lib.dto._changeable import Changeable
from lib.dto.group import Group
from lib.dto.device import Device
from lib.dto.stat import Stat
from lib.dto.event import Event
from lib.helper import Helper


class CacheDataException(Exception):
    pass

class Cache(): 
    def __init__(self, config):
        self.config = config
        
        self._lock = threading.Lock()
        
        self.groups = {}
        self.devices = {}
        self.stats = {}

        self.ip_mac_map = {}
        self.ip_dns_map = {}
        
    #def getDevice(self, mac):
    #    return self.devices.get(mac, None)
    
    def _eventLog(self, stack, msg):
        [_, file ] = stack[1][1].rsplit("/", 1)
        
        #stack[1][3], 
        logging.info(msg, extra={"_module": "{}:{}".format( file[:-3] , stack[1][2] ) })
    
    def lock(self):
        self._lock.acquire()
        
    def unlock(self):
        self._lock.release()
        
    def getGroups(self):
        return list(self.groups.values())
    
    def getUnlockedGroup(self, gid ):
        return self.groups.get(gid, None)

    def getGroup(self, gid, type, autocreate = True ):
        if gid not in self.groups:
            if not autocreate:
                return None
            group = Group(gid, type)
            self.groups[gid] = group
        else:
            group = self.groups[gid]
        group.lock()
        return group
            
    def confirmGroup(self, group, event_callback ):
        group.unlock()

        [state, change_raw, change_details] = group.confirmModificationState()
        if state == Changeable.NEW:
            event_action = Event.ACTION_CREATE
            self._eventLog(inspect.stack(), "Add group {} - [{}]".format(group, change_details) )
        elif state == Changeable.CHANGED:
            event_action = Event.ACTION_MODIFY
            self._eventLog(inspect.stack(), "Update group {} - [{}]".format(group, change_details) )
        else:
            return
        
        event_callback(Event(Event.TYPE_GROUP, event_action, group, change_raw))
        
    def removeGroup(self, gid, event_callback):
        if gid in self.groups:
            self._eventLog(inspect.stack(), "Remove group {}".format(self.groups[gid]) )
            event_callback(Event(Event.TYPE_GROUP, Event.ACTION_DELETE, self.groups[gid]))
            del self.groups[gid]

    def getDevices(self):
        return list(self.devices.values())

    def getUnlockedDevice(self, mac ):
        return self.devices.get(mac, None)
    
    def getDevice(self, mac, autocreate = True ):
        if mac not in self.devices:
            if not autocreate:
                return None
            device = Device(mac,"device",self)
            self.devices[mac] = device
        else:
            device = self.devices[mac]
        device.lock()
        return device
            
    def confirmDevice(self, device, event_callback ):
        device.unlock()

        [state, change_raw, change_details] = device.confirmModificationState()
        if state == Changeable.NEW:
            event_action = Event.ACTION_CREATE
            self._eventLog(inspect.stack(), "Add device {} - [{}]".format(device, change_details))
        elif state == Changeable.CHANGED:
            event_action = Event.ACTION_MODIFY
            self._eventLog(inspect.stack(), "Update device {} - [{}]".format(device, change_details))
        else:
            return
        
        event_callback(Event(Event.TYPE_DEVICE, event_action, device, change_raw ))
        
    def removeDevice(self, mac, event_callback):
        if mac in self.devices:
            self._eventLog(inspect.stack(), "Remove group {}".format(self.devices[mac]))
            event_callback(Event(Event.TYPE_DEVICE, Event.ACTION_DELETE, self.devices[mac] ))
            del self.devices[mac]
            
    def getStats(self):
        return list(self.stats.values())

    def getUnlockedStat(self, mac, interface = None ):
        id = "{}-{}".format(mac, interface)
        return self.stats.get(id, None)
    
    def getStat(self, mac, interface = None, autocreate = True ):
        id = "{}-{}".format(mac, interface)
        if id not in self.stats:
            if not autocreate:
                return None
            stat = Stat(id, mac, interface)
            self.stats[id] = stat
        else:
            stat = self.stats[id]
        stat.lock()
        return stat
                       
    def confirmStat(self, stat, event_callback ):
        stat.unlock()

        related_device = self.devices.get(stat.getMAC(), None)

        [state, change_raw, change_details] = stat.confirmModificationState()
        if state == Changeable.NEW:
            event_action = Event.ACTION_CREATE
            self._eventLog(inspect.stack(), "Add stat {} - [{}]".format(stat.toStr(related_device), change_details))
        elif state == Changeable.CHANGED:
            event_action = Event.ACTION_MODIFY
            self._eventLog(inspect.stack(), "Update stat {} - [{}]".format(stat.toStr(related_device), change_details))
        else:
            return

        event_callback(Event(Event.TYPE_STAT, event_action, stat, change_raw))

    def removeStat(self, mac, interface, event_callback):
        id = "{}-{}".format(mac, interface)
        if id in self.stats:
            related = self.devices.get(mac, None)
            self._eventLog(inspect.stack(), "Remove stat {}".format( "for device {}".format(related) if related else self.stats[id] ) )
            event_callback(Event(Event.TYPE_STAT, Event.ACTION_DELETE, self.stats[id]))
            del self.stats[id]

    def ip2mac(self,ip):
        now = datetime.now()
        if ip not in self.ip_mac_map or (now - self.ip_mac_map[ip][1]).total_seconds() > self.config.cache_ip_mac_revalidation_interval:
            mac = Helper.ip2mac(ip)
            if mac is None:
                return None
            self.ip_mac_map[ip] = [mac, now]

        return self.ip_mac_map[ip][0]
    
    def nslookup(self,ip):
        now = datetime.now()
        if ip not in self.ip_dns_map or (now - self.ip_dns_map[ip][1]).total_seconds() > self.config.cache_ip_dns_revalidation_interval:
            dns = Helper.nslookup(ip)
            if dns is None:
                return None
            self.ip_dns_map[ip] = [dns, now]

        return self.ip_dns_map[ip][0]
