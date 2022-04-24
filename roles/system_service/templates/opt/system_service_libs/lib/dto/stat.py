from lib.dto._changeable import Changeable
from datetime import datetime


class Stat(Changeable):
    def __init__(self, id, mac, interface):
        super().__init__()
        
        self.id = id
        
        self.mac = mac
        self.interface = interface
        
        self.in_bytes = None
        self.in_avg = None
        self.out_bytes = None
        self.out_avg = None
        self.in_speed = None
        self.out_speed = None

        self.offline_since = datetime.now() if interface is None else None
        
        self.details = {}
        
        # internal variables without change detection
        self.last_seen = datetime.now()

    def getID(self):
        return self.id
        
    def getMAC(self):
        return self.mac

    def getInterface(self):
        return self.interface
        
    def getInBytes(self):
        return self.in_bytes

    def setInBytes(self,bytes):
        if self.in_bytes != bytes:
            self._markAsChanged("in_bytes", "in bytes")
            self.in_bytes = bytes

    def getInAvg(self):
        return self.in_avg

    def setInAvg(self,bytes):
        if self.in_avg != bytes:
            self._markAsChanged("in_avg", "in avg")
            self.in_avg = bytes
   
    def getOutBytes(self):
        return self.out_bytes

    def setOutBytes(self,bytes):
        if self.out_bytes != bytes:
            self._markAsChanged("out_bytes", "out bytes")
            self.out_bytes = bytes

    def getOutAvg(self):
        return self.in_avg

    def setOutAvg(self,bytes):
        if self.out_avg != bytes:
            self._markAsChanged("out_avg", "out avg")
            self.out_avg = bytes

    def setInSpeed(self,speed):
        if self.in_speed != speed:
            self._markAsChanged("in_speed", "in speed")
            self.in_speed = speed

    def setOutSpeed(self,speed):
        if self.out_speed != speed:
            self._markAsChanged("out_speed", "out speed")
            self.out_speed = speed

    def setOnline(self,flag):
        if flag:
            self.last_seen = datetime.now()
            offline_since = None
        else:
            offline_since = self.last_seen
        
        if self.offline_since != offline_since:
            self._markAsChanged( "online_state", "offline" if offline_since else "online")
            self.offline_since = offline_since
            
    def isOnline(self):
        return self.offline_since is None

    def getLastSeen(self):
        return self.last_seen

    def setDetail(self, key, value, fmt):
        if key not in self.details or self.details[key]["value"] != value:
            self._markAsChanged(key, "{}{}".format( "add " if key not in self.details else "", key))
            self.details[key] = { "value": value, "format": fmt }
        
    def getDetail(self, key):
        if key in self.details:
            return self.details[key]["value"]
        return None

    def removeDetail(self, key):
        if key in self.details:
            self._markAsChanged(key, "remove {}".format(key))
            del self.details[key]
        
    def getSerializeable(self):
        _stat = {
            "mac": self.mac,
            "interface": self.interface,
            "offline_since": self.offline_since.astimezone().isoformat('T') if self.offline_since is not None else None,
            "details": self.details
        }
            
        if self.in_speed is not None:
            _stat["speed"] = {
                "in": self.in_speed,
                "out": self.out_speed
            }
      
        if self.in_bytes is not None:
            _stat["traffic"] = {
                "in_total": self.in_bytes,
                "in_avg": self.in_avg,
                "out_total": self.out_bytes,
                "out_avg": self.out_avg
            }
            
        return _stat
            
    def toStr(self, related_device):
        return "{}{}".format(related_device,":{}".format(self.interface) if self.interface else "")

    def __repr__(self, related_device = None ):
        return "{}{}".format(self.mac,":{}".format(self.interface) if self.interface else "")
