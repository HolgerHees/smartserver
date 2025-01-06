from datetime import datetime

from lib.scanner.dto._changeable import Changeable
from lib.scanner.dto.event import Event


class ConnectionStatDetails(Changeable):
    def __init__(self, connection_stat, connection_details):
        super().__init__(None, True)
        
        self.connection_stat = connection_stat
        
        self.connection_details = connection_details
        
        self.in_bytes = None
        self.in_avg = None
        self.out_bytes = None
        self.out_avg = None
        self.in_speed = None
        self.out_speed = None
        
    def _checkLock(self):
        self.connection_stat._checkLock()
        
    def _markAsChanged(self, type, details = None):
        self.connection_stat._markAsChanged(type,details)
        
    def reset(self):
        self.setInAvg(0)
        self.setOutAvg(0)
        self.setInBytes(0)
        self.setOutBytes(0)
        self.setInSpeed(0)
        self.setOutSpeed(0)
        for key in list(self._getDetails()):
            self.removeDetail(key)

    def getInBytes(self):
        return self.in_bytes

    def setInBytes(self,bytes):
        self._checkLock()
        if self.in_bytes != bytes:
            self._markAsChanged("in_bytes", "in bytes")
            self.in_bytes = bytes
            return True
        return False

    def getInAvg(self):
        return self.in_avg

    def setInAvg(self,bytes):
        self._checkLock()
        if self.in_avg != bytes:
            self._markAsChanged("in_avg", "in avg")
            self.in_avg = bytes
            return True
        return False
   
    def getOutBytes(self):
        return self.out_bytes

    def setOutBytes(self,bytes):
        self._checkLock()
        if self.out_bytes != bytes:
            self._markAsChanged("out_bytes", "out bytes")
            self.out_bytes = bytes
            return True
        return False

    def getOutAvg(self):
        return self.in_avg

    def setOutAvg(self,bytes):
        self._checkLock()
        if self.out_avg != bytes:
            self._markAsChanged("out_avg", "out avg")
            self.out_avg = bytes
            return True
        return False

    def setInSpeed(self,speed):
        self._checkLock()
        if self.in_speed != speed:
            self._markAsChanged("in_speed", "in speed")
            self.in_speed = speed
            return True
        return False

    def setOutSpeed(self,speed):
        self._checkLock()
        if self.out_speed != speed:
            self._markAsChanged("out_speed", "out speed")
            self.out_speed = speed
            return True
        return False
            
    def getConnectionDetail(self, key, fallback = None):
        return self.connection_details[key] if key in self.connection_details else fallback

class ConnectionStat(Changeable):
    def __init__(self, cache, target_mac, target_interface):
        super().__init__(cache)
        
        self.target_mac = target_mac
        self.target_interface = target_interface

        self.data = {}

    def getEventType(self):
        return Event.TYPE_CONNECTION_STAT

    def getTargetMAC(self):
        return self.target_mac

    def getTargetInterface(self):
        return self.target_interface
    
    def getUnlockedDevice(self):
        devices = list(filter(lambda d: d.getConnection() and d.getConnection().getTargetMAC() == self.target_mac and d.getConnection().getTargetInterface() == self.target_interface, (self._getCache().getDevices()) ))
        return devices[0] if len(devices) == 1 else None
    
    def _buildKey(self, connection_details = None):
        if connection_details is not None:
            _parts = []
            for key in sorted(connection_details.keys()):
                _parts.append("{}:{}".format(key,connection_details[key]))
            key = "-".join(_parts)
        else:
            key = "default"
            
        return key
    
    def getData(self, connection_details = None):
        key = self._buildKey(connection_details)
        if key not in self.data:
            self.data[key] = ConnectionStatDetails(self, connection_details)
        return self.data[key]

    def removeData(self, connection_details = None):
        key = self._buildKey(connection_details)
        if key in self.data:
            del self.data[key]

    def getDataList(self):
        return self.data.values()

    def getSerializeable(self):
        _stat = {
            "mac": self.target_mac,
            "interface": self.target_interface,
            "data": []
        }
        
        for detail in self.data.values():
            _stat["data"].append({
                "connection_details": detail.connection_details,
                "speed": {
                    "in": detail.in_speed,
                    "out": detail.out_speed
                },
                "traffic": {
                    "in_total": detail.in_bytes,
                    "in_avg": detail.in_avg,
                    "out_total": detail.out_bytes,
                    "out_avg": detail.out_avg
                },
                "details": detail._getDetails()
            })
        return _stat
            
    def __repr__(self):
        source_device = self._getCache().getUnlockedDevice(self.target_mac)
        target_device = self._getCache().getUnlockedDevice(self.target_interface)
        return "{} <= {}".format(source_device if source_device is not None else self.target_mac, target_device if target_device is not None else self.target_interface)
