class Group():
    def __init__(self, gid, type):
        self.gid = gid
        self.type = type
        
        self.details = {}

    def getGID(self):
        return self.gid
    
    def appendDetails(self, key, value):
        self.details[key] = value
        
    def getSerializeable(self):
        return {
            "gid": self.gid,
            "type": self.type,
            "details": self.details
        }
      
      
