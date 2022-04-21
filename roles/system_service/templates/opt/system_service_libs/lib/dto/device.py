import logging

from lib.dto._changeable import Changeable


class Connection():
    ETHERNET = "ethernet"
    WIFI = "wifi"
    VIRTUAL = "virtual"
    
    INTERFACE_DEFAULT = "default"
    
    def __init__(self, type, vlan, target_mac, target_interface ):
        self.type = type
        self.vlans = [ vlan ]
        self.target_mac = target_mac
        self.target_interface = target_interface
            
    def getType(self):
        return self.type
            
    def getVLANs(self):
        return self.vlans

    def addVLAN(self, vlan):
        self.vlans.append(vlan)

    def setVLAN(self, vlan):
        self.vlans = [ vlan ]

    def hasVLAN(self, vlan):
        return vlan in self.vlans

    def removeVLAN(self, vlan):
        self.vlans.remove(vlan)

    def getTargetMAC(self):
        return self.target_mac

    def getTargetInterface(self):
        return self.target_interface

    def toStr(self, related_device ):
        return "{} => {}:{}".format(related_device,self.target_mac,self.target_interface)
    
    def getSerializeable(self):
        return { "vlans": self.vlans, "type": self.type, "target_mac": self.target_mac, "target_interface": self.target_interface }
    
    def __repr__(self):
        return "{} => {}:{}".format(self.type,self.target_mac,self.target_interface)
    
class Device(Changeable):
    def __init__(self, mac, type, cache):
        super().__init__()

        self.cache = cache

        self.mac = mac
        self.type = type
        
        self.ip = None
        self.dns = None
        self.info = None
        
        self.hop_connections = []
        self.connection = None
        
        self.gids = []
        
        self.services = {}
        self.details = {}

        # internal variables without change detection
        self.virtual_connection = None
        self.supports_wifi = False

    def getMAC(self):
        return self.mac

    def getType(self):
        return self.type

    def setType(self, type):
        self.type = type

    def getIP(self):
        return self.ip
        
    def setIP(self, ip):
        if self.ip != ip:
            self._markAsChanged("ip")
            self.ip = ip

    def getInfo(self):
        return self.info

    def setInfo(self, info):
        if self.info != info:
            self._markAsChanged("info")
            self.info = info

    def getDNS(self):
        return self.dns

    def setDNS(self, dns):
        if self.dns != dns:
            self._markAsChanged("dns")
            self.dns = dns

    def getDNS(self):
        self.dns

    def addHopConnection(self, type, vlan, target_mac, target_interface, target_device = None):
        if type == Connection.WIFI:
            _connections = list(filter(lambda c: c.getType() == type, self.hop_connections ))
        else:
            _connections = list(filter(lambda c: c.getTargetMAC() == target_mac and c.getTargetInterface() == target_interface, self.hop_connections ))

        if len(_connections) > 0:
            _connection = _connections[0]
            if _connection.getType() != type:
                raise Exception("Wrong connection type")
            
            if _connection.hasVLAN(vlan):
                return
            
            if type == Connection.WIFI:
                _connection.setVLAN(vlan)
            else:
                _connection.addVLAN(vlan)
        else:
            if type == Connection.WIFI:
                self.supports_wifi = True
                
            self.hop_connections.append(Connection(type, vlan, target_mac, target_interface))

        self._detectConnection()

        self._markAsChanged("connection", "add connection to {}:{}".format(target_device if target_device else target_mac,vlan))    
        
        
       
    def removeHopConnection(self, vlan, target_mac, target_interface):
        _connections = list(filter(lambda c: c.getTargetMAC() == target_mac and c.getTargetInterface() == target_interface, self.hop_connections ))
        if len(_connections) > 0:
            _connection = _connections[0]
            if not _connection.hasVLAN(vlan):
                return
            
            _connection.removeVLAN(vlan)
            if len(_connection.getVLANs()) == 0:
                self.hop_connections.remove(_connection)
            
            if _connection == self.connection:
                self._detectConnection()

            self._markAsChanged("connection", "remove connection from {}:{}".format(target_mac, vlan))            
            
    def getHopConnections(self):
        return list(self.hop_connections)

    def setVirtualConnection(self, connection):
        self.virtual_connection = connection
        
    def getConnection(self):
        return self.virtual_connection if self.virtual_connection is not None else self.connection

    def _detectConnection(self):
        devices = self.cache.getDevices()
        
        connections = self.getHopConnections();
        
        #print("-------------_" + self.ip)
        related_macs = []
        for _connection in connections:
            related_devices = list(filter(lambda d: d.getMAC() == _connection.getTargetMAC(), devices ))
            for related_device in related_devices:
                for related_connection in related_device.getHopConnections():
                    if related_connection.getTargetMAC() == related_device.getMAC():
                        continue
                    related_macs.append(related_connection.getTargetMAC())
        #        print( " - " + _connection.getTargetMAC())
        #print( related_macs )

        connection = None
        for _connection in connections:
            if _connection.getTargetMAC() in related_macs:
                continue
            
            connection = _connection
            break
        
        if connection is None:
            logging.info(self)
            for _connection in connections:
                logging.info(_connection)
                
        self.connection = connection

    def supportsWifi(self):
        return self.supports_wifi

    def addGID(self, gid):
        if gid not in self.gids:
            self._markAsChanged("gid", "add gid")
            self.gids.append(gid)

    def removeGID(self, gid):
        if gid in self.gids:
            self._markAsChanged("gid", "remove gid")
            self.gids.remove(gid)
            
    def getGIDs(self):
        return self.gids

    def setDetail(self, key, value):
        if key not in self.details or self.details[key] != value:
            self._markAsChanged(key, "{}{}".format( "add " if key not in self.details else "", key))
            self.details[key] = value

    def removeDetail(self, key):
        if key in self.details:
            self._markAsChanged(key, "remove {}".format(key))
            del self.details[key]
            
    def setServices(self, services):
        self._markAsChanged("services")
        self.services = services

    def getSerializeable(self, devices ):
        
        #if not connection:
        #    print("NO CONNECTION")
        #print( connection )

        connection = self.getConnection()

        return {
            "mac": self.mac,
            "type": self.type,

            "ip": self.ip,
            "dns": self.dns,
            "info": self.info,
            
            "connection": connection.getSerializeable() if connection else None,

            "gids": self.gids,

            "services": self.services,
            "details": self.details
        }
    
    def __repr__(self):
        if self.ip:
            return self.ip
        else:
            return self.mac
      
      
