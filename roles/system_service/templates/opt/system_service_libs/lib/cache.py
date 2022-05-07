import threading
import sys
from datetime import datetime
import time
import logging

from lib.dto._changeable import Changeable
from lib.dto.group import Group
from lib.dto.device import Device, Connection
from lib.dto.device_stat import DeviceStat
from lib.dto.connection_stat import ConnectionStat
from lib.dto.event import Event
from lib.helper import Helper


class CacheDataException(Exception):
    pass

class Cache(): 
    def __init__(self, config):
        self.config = config
        
        self._lock = threading.Lock()
        self._lock_owner = None
        
        self.groups = {}
        self.devices = {}
        self.stats = {}

        self.ip_mac_map = {}
        self.ip_dns_map = {}

        self.gateway_mac = None

        while True:
            self.gateway_mac = self.ip2mac(self.config.default_gateway_ip)
            if self.gateway_mac is not None:
                break
            logging.info("Waiting for gateway {}".format(self.config.default_gateway_ip))
            time.sleep(1)
            
        logging.info("Gateway initialized")
        
    def getGatewayMAC(self):
        return self.gateway_mac
    
    def getGatewayInterface(self, vlan):
        return "lan{}".format(vlan)
    
    def getGatewayConnection(self):
        return Connection(Connection.ETHERNET, self.config.default_vlan, self.getGatewayMAC(), self.getGatewayInterface(self.config.default_vlan))

    def getWanMAC(self):
        return "00:00:00:00:00:00"
    
    def getWanInterface(self):
        return "wan"
    
    def lock(self, owner):
        self._lock.acquire()
        self._lock_owner = owner
        
    def unlock(self, owner):
        self._lock.release()
        self._lock_owner = None
        
    def cleanLocks(self, owner, events):
        if self._lock_owner != owner:
            return
        
        for group in self.getGroups():
            if not group.isLocked():
                continue
            self.confirmGroup(group, lambda event: events.append(event))
        
        for device in self.getDevices():
            if not device.isLocked():
                continue
            self.confirmDevice(device, lambda event: events.append(event))

        for stat in self.getStats():
            if not stat.isLocked():
                continue
            self.confirmStat(stat, lambda event: events.append(event))

        self.unlock(owner)
    
    def _checkLock(self):
        if self._lock_owner is None:
            raise Exception("Cache not locked")
        
    def getGroups(self):
        return list(self.groups.values())
    
    def getUnlockedGroup(self, gid ):
        return self.groups.get(gid, None)

    def getGroup(self, gid, type):
        self._checkLock()

        if gid not in self.groups:
            group = Group(self, gid, type)
            self.groups[gid] = group
        else:
            group = self.groups[gid]
            
        group.lock(self._lock_owner)
        return group
            
    def confirmGroup(self, group, event_callback ):
        self._checkLock()

        group.unlock(self._lock_owner)

        [state, change_raw, change_details] = group.confirmModificationState()
        if state == Changeable.NEW:
            event_action = Event.ACTION_CREATE
            Helper.logEvent(sys._getframe(1), "Add group {} - [{}]".format(group, change_details) )
        elif state == Changeable.CHANGED:
            event_action = Event.ACTION_MODIFY
            Helper.logEvent(sys._getframe(1), "Update group {} - [{}]".format(group, change_details) )
        else:
            return
        
        event_callback(Event(Event.TYPE_GROUP, event_action, group, change_raw))
        
    def removeGroup(self, gid, event_callback):
        self._checkLock()

        if gid in self.groups:
            Helper.logEvent(sys._getframe(1), "Remove group {}".format(self.groups[gid]) )
            event_callback(Event(Event.TYPE_GROUP, Event.ACTION_DELETE, self.groups[gid]))
            del self.groups[gid]

    def getDevices(self):
        return list(self.devices.values())

    def getUnlockedDevice(self, mac ):
        return self.devices.get(mac, None)
    
    def getDevice(self, mac):
        self._checkLock()
        
        if mac not in self.devices:
            device = Device(self, mac,"device")
            self.devices[mac] = device
        else:
            device = self.devices[mac]

        device.lock(self._lock_owner)

        return device
            
    def confirmDevice(self, device, event_callback ):
        self._checkLock()

        device.unlock(self._lock_owner)

        [state, change_raw, change_details] = device.confirmModificationState()
        if state == Changeable.NEW:
            event_action = Event.ACTION_CREATE
            Helper.logEvent(sys._getframe(1), "Add device {} - [{}]".format(device, change_details))
        elif state == Changeable.CHANGED:
            event_action = Event.ACTION_MODIFY
            Helper.logEvent(sys._getframe(1), "Update device {} - [{}]".format(device, change_details))
        else:
            return
        
        event_callback(Event(Event.TYPE_DEVICE, event_action, device, change_raw ))
        
    def removeDevice(self, mac, event_callback):
        self._checkLock()

        if mac in self.devices:
            Helper.logEvent(sys._getframe(1), "Remove group {}".format(self.devices[mac]))
            event_callback(Event(Event.TYPE_DEVICE, Event.ACTION_DELETE, self.devices[mac] ))
            del self.devices[mac]
            
    def getStats(self):
        return list(self.stats.values())

    def getUnlockedDeviceStat(self, mac ):
        return self.getUnlockedConnectionStat(mac, None)
        
    def getUnlockedConnectionStat(self, mac, interface ):
        id = "{}-{}".format(mac, interface)
        return self.stats.get(id, None)
    
    def getDeviceStat(self, mac):
        return self.getConnectionStat(mac, None)
    
    def getConnectionStat(self, mac, interface):
        self._checkLock()

        id = "{}-{}".format(mac, interface)
        if id not in self.stats:
            stat = ConnectionStat(self, mac, interface) if interface is not None else DeviceStat(self, mac)
            self.stats[id] = stat
        else:
            stat = self.stats[id]
            
        stat.lock(self._lock_owner)
        return stat
                       
    def confirmStat(self, stat, event_callback ):
        self._checkLock()

        stat.unlock(self._lock_owner)

        [state, change_raw, change_details] = stat.confirmModificationState()
        if state == Changeable.NEW:
            event_action = Event.ACTION_CREATE
            Helper.logEvent(sys._getframe(1), "Add stat {} - [{}]".format(stat, change_details))
        elif state == Changeable.CHANGED:
            event_action = Event.ACTION_MODIFY
            Helper.logEvent(sys._getframe(1), "Update stat {} - [{}]".format(stat, change_details))
        else:
            return

        event_callback(Event(Event.TYPE_STAT, event_action, stat, change_raw))

    def removeDeviceStat(self, mac, event_callback):
        self._checkLock()

        self.removeInterfaceStat(mac, None, event_callback)
        
    def removeConnectionStat(self, mac, interface, event_callback):
        self._checkLock()

        id = "{}-{}".format(mac, interface)
        if id in self.stats:
            related = self.devices.get(mac, None)
            Helper.logEvent(sys._getframe(1), "Remove stat {}".format( "for device {}".format(related) if related else self.stats[id] ) )
            event_callback(Event(Event.TYPE_STAT, Event.ACTION_DELETE, self.stats[id]))
            del self.stats[id]

    def ip2mac(self,ip):
        now = datetime.now()
        if ip not in self.ip_mac_map or (now - self.ip_mac_map[ip][1]).total_seconds() > self.config.cache_ip_mac_revalidation_interval:
            mac = Helper.ip2mac(ip, self.config.main_interface)
            if mac is None:
                logging.info("Not able to resolve ip2mac. Fallback to ping")
                # try a ping to force an arp table update
                mac = Helper.ping(ip, self.config.main_interface)
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
