class Stats():
    def __init__(self, target, type):
        self.target = target
        self.type = type
        
        self.in_bytes = 0
        self.in_avg = 0
        self.out_bytes = 0
        self.out_avg = 0
        self.in_speed = 0
        self.out_speed = 0

        self.offline_since = None

        self.details = {}
        
    def setType(self, type ):
        self.type = type

    def getType(self):
        return self.type
        
    def setTarget(self, target ):
        self.target = target

    def getTarget(self):
        return self.target

    def setInBytes(self,bytes):
        self.in_bytes = bytes

    def setInAvg(self,bytes):
        self.in_avg = bytes

    def setOutBytes(self,bytes):
        self.out_bytes = bytes

    def setOutAvg(self,bytes):
        self.in_avg = bytes

    def setInSpeed(self,speed):
        self.in_speed = speed

    def setOutSpeed(self,speed):
        self.out_speed = speed

    def setOfflineSince(self,offline_since):
        self.offline_since = offline_since

    def appendDetails(self, key, value):
        self.details[key] = value
        
    def getSerializeable(self, uid):
        return {
            "uid": uid,
            "traffic": {
                "in_total": self.in_bytes,
                "in_avg": self.in_avg,
                "out_total": self.out_bytes,
                "out_avg": self.out_avg
            },
            "speed": {
                "in": self.in_speed,
                "out": self.out_speed
            },
            "offline_since": self.offline_since.astimezone().isoformat('T') if self.offline_since is not None else None,
            "details": self.details
        }
      
    def __repr__(self):
        return "{} ({})".format(self.target,self.type)
