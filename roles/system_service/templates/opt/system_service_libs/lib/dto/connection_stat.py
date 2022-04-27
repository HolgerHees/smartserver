from lib.dto._changeable import Changeable
from datetime import datetime


class ConnectionStat(Changeable):
    def __init__(self, cache, mac, interface):
        super().__init__(cache)
        
        self.mac = mac
        self.interface = interface
        
        self.in_bytes = None
        self.in_avg = None
        self.out_bytes = None
        self.out_avg = None
        self.in_speed = None
        self.out_speed = None

        self.details = {}

    def getMAC(self):
        return self.mac

    def getInterface(self):
        return self.interface
    
    def getUnlockedDevice(self):
        devices = list(filter(lambda d: d.getConnection() and d.getConnection().getTargetMAC() == self.mac and d.getConnection().getTargetInterface() == self.interface, (self._getCache().getDevices()) ))
        return devices[0] if len(devices) == 1 else None
    
    def getInBytes(self):
        return self.in_bytes

    def setInBytes(self,bytes):
        self._checkLock()
        if self.in_bytes != bytes:
            self._markAsChanged("in_bytes", "in bytes")
            self.in_bytes = bytes

    def getInAvg(self):
        return self.in_avg

    def setInAvg(self,bytes):
        self._checkLock()
        if self.in_avg != bytes:
            self._markAsChanged("in_avg", "in avg")
            self.in_avg = bytes
   
    def getOutBytes(self):
        return self.out_bytes

    def setOutBytes(self,bytes):
        self._checkLock()
        if self.out_bytes != bytes:
            self._markAsChanged("out_bytes", "out bytes")
            self.out_bytes = bytes

    def getOutAvg(self):
        return self.in_avg

    def setOutAvg(self,bytes):
        self._checkLock()
        if self.out_avg != bytes:
            self._markAsChanged("out_avg", "out avg")
            self.out_avg = bytes

    def setInSpeed(self,speed):
        self._checkLock()
        if self.in_speed != speed:
            self._markAsChanged("in_speed", "in speed")
            self.in_speed = speed

    def setOutSpeed(self,speed):
        self._checkLock()
        if self.out_speed != speed:
            self._markAsChanged("out_speed", "out speed")
            self.out_speed = speed

    def getSerializeable(self):
        _stat = {
            "mac": self.mac,
            "interface": self.interface,
            "speed": {
                "in": self.in_speed,
                "out": self.out_speed
            },
            "traffic": {
                "in_total": self.in_bytes,
                "in_avg": self.in_avg,
                "out_total": self.out_bytes,
                "out_avg": self.out_avg
            },
            "details": self._getDetails()
        }
        return _stat
            
    def __repr__(self):
        device = self._getCache().getUnlockedDevice(self.mac)
        return "{}:{}".format(device if device is not None else self.mac,self.interface)
