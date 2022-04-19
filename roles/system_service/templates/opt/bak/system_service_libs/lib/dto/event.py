class Event():   
    TYPE_GROUP = "group"
    TYPE_DEVICE = "device"
    TYPE_DEVICE_STAT = "device_stat"
    TYPE_PORT_STAT = "port_stat"

    ACTION_CREATE = "create"
    ACTION_MODIFY = "modify"
    ACTION_DELETE = "delete"

    ACTION_SKIP = "skip"

    def __init__(self, type, identifier, payload ):
        self.type = type
        self.action = Event.ACTION_SKIP
        self.identifier = identifier
        self.payload = payload

    def getType(self):
        return self.type
        
    def setAction(self, action):
        self.action = action

    def getAction(self):
        return self.action;

    def getIdentifier(self):
        return self.identifier
    
    def getPayload(self, pid):
        return self.payload.get(pid, None) 

    def __repr__(self):
        return "{}-{}".format(self.type, self.action)
