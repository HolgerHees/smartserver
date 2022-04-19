class Device():
    CONNECTION_TYPE_ETHERNET = "ethernet"
    CONNECTION_TYPE_WIFI = "wifi"
    CONNECTION_TYPE_VIRTUAL = "virtual"
    
    def __init__(self, uid, type):
        self.uid = uid
        self.type = type
        self._type = type
        
        self.mac = None
        self.ip = None
        self.dns = None
        self.info = None
        
        self.connection_target_uid = None
        self.connection_target_port = None
        self.connection_type = None
        self.connection_vlan = None
        
        self.gids = []
        
        self.ports = {}
        self.services = {}
        self.details = {}

    def getUID(self):
        return self.uid;

    def setType(self, type):
        self.type = self._type if type is None else type

    def getMAC(self):
        return self.mac

    def setMAC(self, mac):
        self.mac = mac

    def getIP(self):
        return self.ip
        
    def setIP(self, ip):
        self.ip = ip

    def setInfo(self, info):
        self.info = info

    def setDNS(self, dns):
        self.dns = dns

    def getDNS(self):
        self.dns

    def addGID(self, gid):
        self.gids.append(gid)

    def removeGID(self, gid):
        self.gids.remove(gid)

    def appendService(self, port, service):
        self.services[port] = service

    def resetPorts(self):
        self.ports = {}

    def setPort(self, port, name):
        self.ports[port] = name
        
    def setDetail(self, key, value):
        self.details[key] = value

    def removeDetail(self):
        del self.details[key]

    def getConnectionTargetUID(self):
        return self.connection_target_uid
        
    def getConnectionTargetPort(self):
        return self.connection_target_port

    def getConnectionType(self):
        return self.connection_type
    
    def getConnectionVLAN(self):
        return self.connection_vlan

    def setConnectionTarget(self, uid, port, vlan, type):
        if type == Device.CONNECTION_TYPE_VIRTUAL:
            self.connection_virtual_target_uid = uid
            self.connection_virtual_target_port = port
            self.connection_virtual_type = type
            self.connection_virtual_vlan = vlan
        else:
            self.connection_target_uid = uid
            self.connection_target_port = port
            self.connection_type = type
            self.connection_vlan = vlan
            
    def removeConnectionTarget(self, type):
        if type == Device.CONNECTION_TYPE_VIRTUAL:
            self.connection_virtual_target_uid = None
            self.connection_virtual_target_port = None
            self.connection_virtual_type = None
            self.connection_virtual_vlan = None
        elif self.connection_type == type:
            self.connection_target_uid = None
            self.connection_target_port = None
            self.connection_type = None
            self.connection_vlan = None

    def getSerializeable(self):
        return {
            "uid": self.uid,
            "type": self.type,
            "mac": self.mac,
            "ip": self.ip,
            "dns": self.dns,
            "info": self.info,
            
            "connection_target": { 
                "uid": self.connection_virtual_target_uid if self.connection_virtual_target_uid is not None else self.connection_target_uid, 
                "port": self.connection_virtual_target_port if self.connection_virtual_target_port is not None else self.connection_target_port, 
                "type": self.connection_virtual_type if self.connection_virtual_type is not None else self.connection_type,
                "vlan": self.connection_virtual_vlan if self.connection_virtual_vlan is not None else self.connection_vlan,
            },

            "gids": self.gids,

            "ports": self.ports,
            "services": self.services,
            "details": self.details
        }
    
    def __repr__(self):
        if self.ip:
            return self.ip
        elif self.mac:
            return self.mac
        else:
            return self.uid
      
      
