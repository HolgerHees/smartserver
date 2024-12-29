from datetime import datetime

from lib.scanner.dto._changeable import Changeable
from lib.scanner.dto.event import Event


class DeviceStat(Changeable):
    def __init__(self, cache, mac):
        super().__init__(cache)
        
        self.mac = mac
        
        self.is_online = False
        
        self.last_validated_seen = None
        self.last_unvalidated_seen = datetime.now()
        
    def getEventType(self):
        return Event.TYPE_DEVICE_STAT

    def getMAC(self):
        return self.mac

    def getUnlockedDevice(self):
        return self._getCache().getUnlockedDevice(self.mac)
    
    def setLastSeen(self,validated):
        self.last_unvalidated_seen = datetime.now()

        if validated:
            self.last_validated_seen = self.last_unvalidated_seen

            if not self.is_online:
                self._checkLock()

                self._markAsChanged( "online_state", "online")
                self.is_online = True

    def setOffline(self):
        if not self.is_online:
            return

        self._checkLock()

        self._markAsChanged( "online_state", "offline")
        self.is_online = False

    def isOnline(self):
        return self.is_online

    def getValidatedLastSeen(self):
        return self.last_validated_seen

    def getUnvalidatedLastSeen(self):
        return self.last_unvalidated_seen

    def getSerializeable(self):
        _stat = {
            "mac": self.mac,
            "is_online": 1 if self.is_online else 0,
            "last_seen": self.last_validated_seen.astimezone().isoformat('T') if self.last_validated_seen is not None else self.last_unvalidated_seen.astimezone().isoformat('T'),
            "details": self._getDetails()
        }
            
        return _stat
            
    def __repr__(self):
        device = self._getCache().getUnlockedDevice(self.mac)
        return "{}".format(device if device is not None else self.mac)
