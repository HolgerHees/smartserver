from datetime import datetime

from lib.scanner.dto._changeable import Changeable
from lib.scanner.dto.event import Event


class DeviceStat(Changeable):
    def __init__(self, cache, mac):
        super().__init__(cache)
        
        self.mac = mac
        
        self.offline_since = datetime.now()
        
        # internal variables without change detection
        self.last_validated_seen = None
        self.last_unvalidated_seen = datetime.now()
        
    def getEventType(self):
        return Event.TYPE_DEVICE_STAT

    def getMAC(self):
        return self.mac

    def getUnlockedDevice(self):
        return self._getCache().getUnlockedDevice(self.mac)
    
    def setLastSeen(self,validated):
        if validated:
            self.last_validated_seen = datetime.now()
        self.last_unvalidated_seen = datetime.now()

    def setOnline(self,flag):
        self._checkLock()
        if flag:
            offline_since = None
        else:
            offline_since = self.last_validated_seen
        
        if self.offline_since != offline_since:
            self._markAsChanged( "online_state", "offline" if offline_since else "online")
            self.offline_since = offline_since
            return True
        return False
            
    def isOnline(self):
        return self.offline_since is None

    def isValidated(self):
        return self.last_validated_seen is not None

    def getValidatedLastSeen(self):
        return self.last_validated_seen

    def getUnvalidatedLastSeen(self):
        return self.last_unvalidated_seen

    def getSerializeable(self):
        _stat = {
            "mac": self.mac,
            "offline_since": self.offline_since.astimezone().isoformat('T') if self.offline_since is not None else None,
            "details": self._getDetails()
        }
            
        return _stat
            
    def __repr__(self):
        device = self._getCache().getUnlockedDevice(self.mac)
        return "{}".format(device if device is not None else self.mac)
