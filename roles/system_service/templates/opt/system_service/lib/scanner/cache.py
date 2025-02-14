import threading
import sys
from datetime import datetime
import time
import logging
from collections import deque

from lib.scanner.dto._changeable import Changeable
from lib.scanner.dto.group import Group
from lib.scanner.dto.device import Device, Connection
from lib.scanner.dto.device_stat import DeviceStat
from lib.scanner.dto.connection_stat import ConnectionStat
from lib.scanner.dto.event import Event
from lib.scanner.helper import Helper


class CacheDataException(Exception):
    pass

class Cache(): 
    def __init__(self, config):
        self.config = config
        
        self._lock = threading.Lock()
        self._lock_source = None
        self._lock_owner = None
        self._lock_start = None

        self.groups = {}
        self.devices = {}
        self.stats = {}

        self.ip_mac_map = {}
        self.ip_dns_map = {}

        self.gateway_mac = None

        self.event_queue = deque()
        self.event_trigger = threading.Event()

        while True:
            self.gateway_mac = self.ip2mac(self.config.default_gateway_ip)
            if self.gateway_mac is not None:
                break
            logging.info("Waiting for gateway {}".format(self.config.default_gateway_ip))
            time.sleep(1)
            
        logging.info("Gateway initialized")

    def getEventQueue(self):
        return self.event_queue
        
    def getEventTrigger(self):
        return self.event_trigger

    def _dispatchEvent(self, source_handler, events):
        self.event_queue.append([source_handler,events])

    def getGatewayMAC(self):
        return self.gateway_mac
    
    def getGatewayInterface(self, vlan):
        return "lan.{}".format(vlan)
    
    def getWanMAC(self):
        return "00:00:00:00:00:00"
    
    def getWanInterface(self):
        return "wan"
    
    def lock(self, owner):
        #Helper.logInfo("LOCKDEBUG: lock", 2)
        if not self._lock.acquire(timeout=60):
            raise Exception("Not able to aquire lock. TIMEOUT: 60 seconds, REQUESTING OWNER: {}, ACTIVE OWNER: {}, OWNER SOURCE: {}".format(owner, self._lock_owner, self._lock_source))

        frame = sys._getframe(1)
        self._lock_source = "{}:{}".format( frame.f_code.co_filename.replace("/",".")[:-3] , frame.f_lineno )
        self._lock_owner = owner
        self._lock_start = time.time()

        #logging.info(">>>>>>>>>> CACHE LOCK {}".format(self._lock_owner))

    def unlock(self, owner):
        if self._lock_owner != owner:
            raise Exception("Not able to unlock. REQUESTING OWNER: {}, ACTIVE OWNER: {}, OWNER SOURCE: {}".format(owner, self._lock_owner, self._lock_source))
            return

        duration = time.time() - self._lock_start

        if duration > 5.0:
            logging.warning("Cache was {:.2f} seconds locked: ACTIVE OWNER: {}, OWNER SOURCE: {}".format(duration, self._lock_owner, self._lock_source))

        self._lock.release()
        self._lock_source = None
        self._lock_owner = None
        self._lock_start = None

        self.event_trigger.set()

    def cleanLocks(self, owner):
        if self._lock_owner != owner:
            return
        
        for group in self.getGroups():
            if not group.isLocked():
                continue
            self.confirmGroup(owner, group, 2)
        
        for device in self.getDevices():
            if not device.isLocked():
                continue
            self.confirmDevice(owner, device, 2)

        for stat in self.getStats():
            if not stat.isLocked():
                continue
            self.confirmStat(owner, stat, 2)

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
            
    def confirmGroup(self, source_handler, group, caller_frame = 1 ):
        self._checkLock()

        group.unlock(self._lock_owner)

        [state, change_raw, change_details] = group.confirmModificationState()

        if state == Changeable.NEW:
            event_action = Event.ACTION_CREATE
            Helper.logInfo("Add group {} - [{}]".format(group, change_details), caller_frame + 1 )
        elif state == Changeable.CHANGED:
            event_action = Event.ACTION_MODIFY
            Helper.logInfo("Update group {} - [{}]".format(group, change_details), caller_frame + 1 )
        else:
            return None
        
        event = Event(group.getEventType(), event_action, group, change_raw)
        self._dispatchEvent(source_handler,event)
        return event
    
    def removeGroup(self, source_handler, gid, caller_frame = 1):
        self._checkLock()

        if gid in self.groups:
            Helper.logInfo("Remove group {}".format(self.groups[gid]), caller_frame + 1 )

            self._dispatchEvent(source_handler,Event(self.groups[gid].getEventType(), Event.ACTION_DELETE, self.groups[gid]))
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

    def confirmDevice(self, source_handler, device, caller_frame = 1 ):
        self._checkLock()

        device.unlock(self._lock_owner)

        [state, change_raw, change_details] = device.confirmModificationState()
        if state == Changeable.NEW:
            event_action = Event.ACTION_CREATE
            Helper.logInfo("Add device {} - [{}]".format(device, change_details), caller_frame + 1)
        elif state == Changeable.CHANGED:
            event_action = Event.ACTION_MODIFY
            Helper.logInfo("Update device {} - [{}]".format(device, change_details), caller_frame + 1)
        else:
            return None
        
        event = Event(device.getEventType(), event_action, device, change_raw )
        self._dispatchEvent(source_handler,event)
        return event
    
    def removeDevice(self, source_handler, mac,  caller_frame = 1):
        self._checkLock()

        if mac in self.devices:
            Helper.logInfo("Remove device {}".format(self.devices[mac]), caller_frame + 1)
            self._dispatchEvent(source_handler,Event(self.devices[mac].getEventType(), Event.ACTION_DELETE, self.devices[mac]))
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

        stat = id = "{}-{}".format(mac, interface)
        if id not in self.stats:
            stat = ConnectionStat(self, mac, interface) if interface is not None else DeviceStat(self, mac)
            self.stats[id] = stat
        else:
            stat = self.stats[id]
            
        stat.lock(self._lock_owner)
        return stat
                       
    def confirmStat(self, source_handler, stat, caller_frame = 1 ):
        self._checkLock()

        stat.unlock(self._lock_owner)

        [state, change_raw, change_details] = stat.confirmModificationState()
        if state == Changeable.NEW:
            event_action = Event.ACTION_CREATE
            Helper.logInfo("Add stat {} - [{}]".format(stat, change_details), caller_frame + 1)
        elif state == Changeable.CHANGED:
            event_action = Event.ACTION_MODIFY
            Helper.logInfo("Update stat {} - [{}]".format(stat, change_details), caller_frame + 1)
        else:
            return None

        event = Event(stat.getEventType(), event_action, stat, change_raw)
        self._dispatchEvent(source_handler,event)
        return event

    def removeDeviceStat(self, source_handler, mac, caller_frame = 1):
        self._checkLock()

        self.removeConnectionStat(source_handler, mac, None, caller_frame + 1)
        
    def removeConnectionStat(self, source_handler, mac, interface, caller_frame = 1):
        self._checkLock()

        id = "{}-{}".format(mac, interface)
        if id in self.stats:
            Helper.logInfo("Remove {} stat {}".format( "device" if interface is None else "connection", self.stats[id] ), caller_frame + 1 )
            self._dispatchEvent(source_handler,Event(self.stats[id].getEventType(), Event.ACTION_DELETE, self.stats[id]))
            del self.stats[id]

    def removeConnectionStatDetails(self, source_handler, mac, interface, connection_details, caller_frame = 1):
        self._checkLock()

        stat = self.getUnlockedConnectionStat(mac,interface)
        if stat is not None:
            if len(stat.getDataList()) == 1:
                self.removeConnectionStat(source_handler, mac,interface, caller_frame + 1)
            else:
                stat.lock(self._lock_owner)
                stat.removeData(connection_details)
                self.confirmStat( source_handler, stat, caller_frame + 1 )

    def ip2mac(self,ip, is_running_callback = None):
        now = datetime.now()
        if ip not in self.ip_mac_map or (now - self.ip_mac_map[ip][1]).total_seconds() > self.config.cache_ip_mac_revalidation_interval:
            mac = Helper.ip2mac(ip)
            if mac is None:
                logging.info("Not able to resolve ip2mac {}. Fallback to ping".format(ip))
                # try a ping to force an arp table update
                mac = Helper.getMacFromPing(ip, 5, is_running_callback)
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
