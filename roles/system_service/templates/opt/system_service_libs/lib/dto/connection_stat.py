from lib.dto._changeable import Changeable
from datetime import datetime

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

        self.details = {}

    def getInBytes(self):
        return self.in_bytes

    def setInBytes(self,bytes):
        self.connection_stat._checkLock()
        if self.in_bytes != bytes:
            self.connection_stat._markAsChanged("in_bytes", "in bytes")
            self.in_bytes = bytes

    def getInAvg(self):
        return self.in_avg

    def setInAvg(self,bytes):
        self.connection_stat._checkLock()
        if self.in_avg != bytes:
            self.connection_stat._markAsChanged("in_avg", "in avg")
            self.in_avg = bytes
   
    def getOutBytes(self):
        return self.out_bytes

    def setOutBytes(self,bytes):
        self.connection_stat._checkLock()
        if self.out_bytes != bytes:
            self.connection_stat._markAsChanged("out_bytes", "out bytes")
            self.out_bytes = bytes

    def getOutAvg(self):
        return self.in_avg

    def setOutAvg(self,bytes):
        self.connection_stat._checkLock()
        if self.out_avg != bytes:
            self.connection_stat._markAsChanged("out_avg", "out avg")
            self.out_avg = bytes

    def setInSpeed(self,speed):
        self.connection_stat._checkLock()
        if self.in_speed != speed:
            self.connection_stat._markAsChanged("in_speed", "in speed")
            self.in_speed = speed

    def setOutSpeed(self,speed):
        self.connection_stat._checkLock()
        if self.out_speed != speed:
            self.connection_stat._markAsChanged("out_speed", "out speed")
            self.out_speed = speed
            
    def getConnectionDetail(self, key):
        return self.connection_details[key] if key in self.connection_details else None

class ConnectionStat(Changeable):
    def __init__(self, cache, mac, interface):
        super().__init__(cache)
        
        self.mac = mac
        self.interface = interface

        self.data = {}

    def getMAC(self):
        return self.mac

    def getInterface(self):
        return self.interface
    
    def getUnlockedDevice(self):
        devices = list(filter(lambda d: d.getConnection() and d.getConnection().getTargetMAC() == self.mac and d.getConnection().getTargetInterface() == self.interface, (self._getCache().getDevices()) ))
        return devices[0] if len(devices) == 1 else None
    
    def getData(self, connection_details = None):
        if connection_details is not None:
            _parts = []
            for key in sorted(connection_details.keys()):
                _parts.append("{}:{}".format(key,connection_details[key]))
            key = "-".join(_parts)
        else:
            key = "default"
    
        if key not in self.data:
            self.data[key] = ConnectionStatDetails(self, connection_details)
        return self.data[key]

    def getDataList(self):
        return self.data.values()

    def getSerializeable(self):
        _stat = {
            "mac": self.mac,
            "interface": self.interface,
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
        device = self._getCache().getUnlockedDevice(self.mac)
        return "{}:{}".format(device if device is not None else self.mac,self.interface)
