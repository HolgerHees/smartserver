from lib.dto._changeable import Changeable


class Group(Changeable):
    WIFI = "wifi"
    
    def __init__(self, cache, gid, type):
        super().__init__(cache)
        
        self.gid = gid
        self.type = type
        
        self.details = {}

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
