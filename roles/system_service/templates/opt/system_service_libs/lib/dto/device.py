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
        self.enabled = True
            
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
    
    def setEnabled(self, enabled):
        self.enabled = enabled

    def isEnabled(self):
        return self.enabled

    def getSerializeable(self):
        return { "vlans": self.vlans, "type": self.type, "target_mac": self.target_mac, "target_interface": self.target_interface }
    
    def __repr__(self):
        return "{} => {}:{}".format(self.type,self.target_mac,self.target_interface)
    
class Device(Changeable):
    def __init__(self, cache, mac, type):
        super().__init__(cache)

        self.mac = mac
        
        self.dns = None
        self.info = None
        
        self.hop_connections = []
        self.connection = None
        
        self.gids = []
        
        self.services = {}

        # internal variables without change detection
        self.virtual_connection = None
        self.supports_wifi = False
        
        self._initPriorizedData(["type", "ip", "dns"])

        self._setPriorizedData("type", "default", 0, type)
        
    def getMAC(self):
        return self.mac

    def getType(self):
        return self._getPriorizedValue("type")

    def setType(self, source, priority, type):
        self._checkLock()
        if self._setPriorizedData("type", source, priority, type):
            self._markAsChanged("type")
            
    def removeType(self, source):
        self._checkLock()
        if self._removePriorizedData("type", source):
            self._markAsChanged("type")
            
    def hasType(self,source):
        return self._hasPriorizedData("type", source)

    def getIP(self):
        return self._getPriorizedValue("ip")
        
    def setIP(self, source, priority, ip):
        self._checkLock()
        if self._setPriorizedData("ip", source, priority, ip):
            self._markAsChanged("ip")
                
    def removeIP(self, source):
        self._checkLock()
        if self._removePriorizedData("ip", source):
            self._markAsChanged("ip")

    def hasIP(self,source):
        return self._hasPriorizedData("ip", source)

    def getDNS(self):
        return self._getPriorizedValue("dns")
        
    def setDNS(self, source, priority, dns):
        self._checkLock()
        if self._setPriorizedData("dns", source, priority, dns):
            self._markAsChanged("dns")
                
    def removeDNS(self, source):
        self._checkLock()
        if self._removePriorizedData("dns", source):
            self._markAsChanged("dns")

    def hasDNS(self,source):
        return self._hasPriorizedData("dns", source)

    def getInfo(self):
        return self.info

    def setInfo(self, info):
        self._checkLock()
        if self.info != info:
            self._markAsChanged("info")
            self.info = info

    def addHopConnection(self, type, vlan, target_mac, target_interface):
        self._checkLock()
        if target_mac == self.cache.getGatewayMAC():
            _connections = list(filter(lambda c: c.getTargetMAC() == target_mac, self.hop_connections ))
            if len(_connections) > 0:
                if _connections[0].getType() != Connection.ETHERNET:
                    return
                else:
                    self.hop_connections.remove(_connections[0])
        
        _connections = list(filter(lambda c: c.getTargetMAC() == target_mac and c.getTargetInterface() == target_interface, self.hop_connections ))

        if len(_connections) > 0:
            _connection = _connections[0]
            if _connection.getType() != type:
                raise Exception("Wrong connection type")
            
            if not _connection.isEnabled():
                _connection.setEnabled(True)
            
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

        #self.connection = None
        
        target_device = self.cache.getUnlockedDevice(target_mac)
        self._markAsChanged("connection", "add connection to {}:{}".format(target_device if target_device else target_mac,vlan))    
       
    def removeHopConnection(self, type, vlan, target_mac, target_interface):
        self._checkLock()
        _connections = list(filter(lambda c: c.getType() == type and c.getTargetMAC() == target_mac and c.getTargetInterface() == target_interface, self.hop_connections ))
        if len(_connections) > 0:
            _connection = _connections[0]
            if not _connection.hasVLAN(vlan):
                return
            
            _connection.removeVLAN(vlan)
            if len(_connection.getVLANs()) == 0:
                self.hop_connections.remove(_connection)
            
            #if _connection == self.connection:
            #    self.connection = None

            target_device = self.cache.getUnlockedDevice(target_mac)
            self._markAsChanged("connection", "remove connection from {}:{}".format(target_device if target_device else target_mac, vlan))            
            
    def disableHopConnection(self, type, target_mac, target_interface):
        _connections = list(filter(lambda c: c.getType() == type and c.getTargetMAC() == target_mac and c.getTargetInterface() == target_interface, self.hop_connections ))
        for connection in _connections:
            connection.setEnabled(False)
            
            target_device = self.cache.getUnlockedDevice(target_mac)
            self._markAsChanged("connection", "disable connection to {}:{}".format(target_device if target_device else target_mac,",".join(str(v) for v in connection.getVLANs())))    

    def cleanDisabledHobConnections(self, type, event_callback):
        _connections = list(filter(lambda c: c.getType() == type and not c.isEnabled(), self.hop_connections ))
        for connection in _connections:
            self.hop_connections.remove(connection)
            
            self.cache.removeConnectionStat(_connection.getTargetMAC(), _connection.getTargetInterface(), event_callback)
            
            target_mac = _connection.getTargetMAC()
            target_device = self.cache.getUnlockedDevice(target_mac)
            self._markAsChanged("connection", "remove disabled connection from {}:{}".format(target_device if target_device else target_mac, ",".join(str(v) for v in connection.getVLANs())))

    def getHopConnections(self):
        return list(self.hop_connections)

    def setVirtualConnection(self, connection):
        self.virtual_connection = connection
        
    def getConnection(self):
        return self.virtual_connection if self.virtual_connection is not None else self.connection
   
    def resetConnection(self):
        self.connection = None
        
    def calculateConnectionPath(self, processed_devices):
        #logging.info("CALCULATE")

        if self.getMAC() in processed_devices:
            return
        
        processed_devices[self.getMAC()] = True
        
        connection = None
        hop_count = 0
        for _connection in self.getHopConnections():
            processed_hops = { self._getCache().getWanMAC(): True, self._getCache().getGatewayMAC(): True }
            _hop_count = self._getGWHopCount(_connection, 0, processed_hops, processed_devices)
            if _hop_count >= hop_count:
                hop_count = _hop_count
                connection = _connection
                
        self.connection = connection

    def _getGWHopCount(self, connection, count, processed_hops, processed_devices ):
        if connection is None:
            return count
        
        count += 1
        
        if connection.getTargetMAC() not in processed_hops:
            processed_hops[connection.getTargetMAC()] = True
            _device = self._getCache().getUnlockedDevice(connection.getTargetMAC())
            if _device.connection is None:
                _device.calculateConnectionPath(processed_devices)
            count = self._getGWHopCount(_device.connection, count, processed_hops, processed_devices)
        
        return count

    def supportsWifi(self):
        return self.supports_wifi

    def addGID(self, gid):
        self._checkLock()
        if gid not in self.gids:
            self._markAsChanged("gid", "add gid")
            self.gids.append(gid)

    def removeGID(self, gid):
        self._checkLock()
        if gid in self.gids:
            self._markAsChanged("gid", "remove gid")
            self.gids.remove(gid)
            
    def getGIDs(self):
        return self.gids
           
    def setServices(self, services):
        self._checkLock()
        self._markAsChanged("services")
        self.services = services

    def getSerializeable(self, devices ):
        connection = self.getConnection()

        return {
            "mac": self.mac,

            "type": self.getType(),
            "ip": self.getIP(),
            "dns": self.getDNS(),
            
            "info": self.info,
            
            "connection": connection.getSerializeable() if connection else None,

            "gids": self.gids,

            "services": self.services,
            "details": self._getDetails()
        }
    
    def __repr__(self):
        ip = self.getIP()
        if ip:
            return ip
        else:
            return self.mac
      
      
