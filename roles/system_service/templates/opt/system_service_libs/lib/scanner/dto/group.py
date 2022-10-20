from lib.scanner.dto._changeable import Changeable
from lib.scanner.dto.event import Event


class Group(Changeable):
    WIFI = "wifi"
    
    def __init__(self, cache, gid, type):
        super().__init__(cache)
        
        self.gid = gid
        self.type = type
        
        self.details = {}

    def getEventType(self):
        return Event.TYPE_GROUP

    def getGID(self):
        return self.gid
    
    def getType(self):
        return self.type

    def getSerializeable(self):
        return {
            "gid": self.gid,
            "type": self.type,
            "details": self._getDetails()
        }
        
    def __repr__(self):
        return "{}".format(self.gid)      
