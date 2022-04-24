from lib.dto._changeable import Changeable


class Group(Changeable):
    WIFI = "wifi"
    
    def __init__(self, gid, type):
        super().__init__()
        
        self.gid = gid
        self.type = type
        
        self.details = {}

    def getGID(self):
        return self.gid
    
    def getType(self):
        return self.type

    def setDetail(self, key, value, fmt):
        if key not in self.details or self.details[key] != value:
            self._markAsChanged(key, "{}{}".format( "add " if key not in self.details else "", key))
            self.details[key] = { "value": value, "format": fmt }
        
    def getDetail(self, key):
        if key in self.details:
            return self.details[key]["value"]
        return None

    def getSerializeable(self):
        return {
            "gid": self.gid,
            "type": self.type,
            "details": self.details
        }
        
    def __repr__(self):
        return "{}".format(self.gid)      
