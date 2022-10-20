class Event():   
    TYPE_GROUP = "group"
    TYPE_DEVICE = "device"
    TYPE_DEVICE_STAT = "device_stat"
    TYPE_CONNECTION_STAT = "connection_stat"

    ACTION_CREATE = "create"
    ACTION_MODIFY = "modify"
    ACTION_DELETE = "delete"

    #ACTION_SKIP = "skip"

    def __init__(self, type, action, object, details = [] ):
        self.type = type
        self.action = action
        self.object = object
        self.details = details
        
    #def getUID(self):
    #    return "{}-{}-{}".format(self.type, self.action)

    def getType(self):
        return self.type
        
    def getAction(self):
        return self.action;

    def getObject(self):
        return self.object
    
    def getDetails(self):
        return self.details

    def hasDetail(self, key):
        return key in self.details

    def __repr__(self):
        return "{}-{}".format(self.type, self.action)
