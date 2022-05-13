import logging

from lib.dto._changeable import Changeable
from lib.dto.event import Event


class Connection():
    ETHERNET = "ethernet"
    WIFI = "wifi"
    VIRTUAL = "virtual"
    
    INTERFACE_DEFAULT = "default"
    
    def __init__(self, type, target_mac, target_interface, details_list ):
        self.type = type
        self.details_list = details_list
        self.target_mac = target_mac
        self.target_interface = target_interface
        self.enabled = True
            
    def getType(self):
        return self.type
            
    def getDetailsList(self):
        return self.details_list

    def addDetails(self, details):
        self.details_list.append(details)

    def hasDetails(self, details):
        for _details in self.details_list:
            if _details == details:
                return True
        return False

    def removeDetails(self, details):
        for _details in list(self.details_list):
            if _details == details:
                self.details_list.remove(_details)
                break

    def getTargetMAC(self):
        return self.target_mac

    def getTargetInterface(self):
        return self.target_interface
    
    def setEnabled(self, enabled):
        self.enabled = enabled

    def isEnabled(self):
        return self.enabled

    def getSerializeable(self):
        return { "type": self.type, "target_mac": self.target_mac, "target_interface": self.target_interface, "details": self.details_list }
    
    def __repr__(self):
        return "{} => {}:{}".format(self.type,self.target_mac,self.target_interface)
    
class Device(Changeable):
    def __init__(self, cache, mac, type):
        super().__init__(cache)

        self.mac = mac
        
        self.info = None
        
        self.hop_connections = []
        self.connection = None
        
        self.services = {}

        # internal variables without change detection
        self.virtual_connection = None
        self.supports_wifi = False
        
        self._initPriorizedData([ 
            {"key": "type", "source": "default", "priority": 0, "value": type},
            {"key": "ip"},
            {"key": "dns"}
        ])
        
    def getEventType(self):
        return Event.TYPE_DEVICE

    def getMAC(self):
        return self.mac

    def getType(self):
        return self._getPriorizedValue("type")

    def setType(self, source, priority, type):
        self._checkLock()
        self._setPriorizedData("type", source, priority, type)
            
    def removeType(self, source):
        self._checkLock()
        self._removePriorizedData("type", source)
            
    def hasType(self,source):
        return self._hasPriorizedData("type", source)

    def getIP(self):
        return self._getPriorizedValue("ip")
        
    def setIP(self, source, priority, ip):
        self._checkLock()
        self._setPriorizedData("ip", source, priority, ip)
                
    def removeIP(self, source):
        self._checkLock()
        self._removePriorizedData("ip", source)

    def hasIP(self,source):
        return self._hasPriorizedData("ip", source)

    def getDNS(self):
        return self._getPriorizedValue("dns")
        
    def setDNS(self, source, priority, dns):
        self._checkLock()
        self._setPriorizedData("dns", source, priority, dns)
                
    def removeDNS(self, source):
        self._checkLock()
        self._removePriorizedData("dns", source)

    def hasDNS(self,source):
        return self._hasPriorizedData("dns", source)

    def getInfo(self):
        return self.info

    def setInfo(self, info):
        self._checkLock()
        if self.info != info:
            self._markAsChanged("info")
            self.info = info

    def addHopConnection(self, type, target_mac, target_interface, details = None ):
        self._checkLock()
        #if target_mac == self.cache.getGatewayMAC():
        #    _connections = list(filter(lambda c: c.getTargetMAC() == target_mac, self.hop_connections ))
        #    if len(_connections) > 0:
        #        if _connections[0].getType() != Connection.ETHERNET:
        #            return
        #        else:
        #            self.hop_connections.remove(_connections[0])
        
        action = "add"

        _connections = list(filter(lambda c: c.getTargetMAC() == target_mac and c.getTargetInterface() == target_interface, self.hop_connections ))
        if len(_connections) > 0:
            _connection = _connections[0]

            if _connection.getType() != type:
                raise Exception("Wrong connection type")
            
            if not _connection.isEnabled():
                _connection.setEnabled(True)
                action = "enable"
            else:
                if _connection.hasDetails(details) or details is None:
                    return
                
                _connection.addDetails(details)
        else:
            if type == Connection.WIFI:
                self.supports_wifi = True
                
            self.hop_connections.append(Connection(type, target_mac, target_interface, [ details ] if details is not None else [] ))

        target_device = self.cache.getUnlockedDevice(target_mac)
        self._markAsChanged("connection", "{} connection to {}:{}".format(action, target_device if target_device else target_mac, details))    

        # *** CLEANUP only needed for added connections and NOT for enabled or unchanged ones ***
        if action == "add":
            _connections = list(filter(lambda c: c.getType() == type and not c.isEnabled(), self.hop_connections ))
            for _connection in _connections:
                self.hop_connections.remove(_connection)
                target_mac = _connection.getTargetMAC()
                target_device = self.cache.getUnlockedDevice(target_mac)
                self._markAsChanged("connection", "remove disabled connection to {}:{}".format(target_device if target_device else target_mac, _connection.getDetailsList() ))

    def removeHopConnection(self, type, target_mac, target_interface, details, disable_last_of_type = False):
        self._checkLock()
        _connections = list(filter(lambda c: c.getType() == type and c.getTargetMAC() == target_mac and c.getTargetInterface() == target_interface, self.hop_connections ))
        if len(_connections) > 0:
            _connection = _connections[0]

            if _connection.hasDetails(details):
                _connection.removeDetails(details)

            action = "remove"
            if len(_connection.getDetailsList()) == 0:
                if disable_last_of_type and len(list(filter(lambda c: c.getType() == type, self.hop_connections ))) == 1:
                    _connection.setEnabled(False)
                    action = "disable"
                else:
                    self.hop_connections.remove(_connection)

            target_device = self.cache.getUnlockedDevice(target_mac)
            self._markAsChanged("connection", "{} connection from {}:{}".format(action, target_device if target_device else target_mac, details))            

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
            _hop_count = 9999 if _connection.getType() == Connection.WIFI else self._getGWHopCount(_connection, 0, processed_hops, processed_devices)
            if _hop_count >= hop_count:
                hop_count = _hop_count
                connection = _connection

        self.connection = connection
        
        #logging.info("{} {}".format(self,len(self.getHopConnections())))

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

            "services": self.services,
            "details": self._getDetails()
        }
    
    def __repr__(self):
        ip = self.getIP()
        if ip:
            return ip
        else:
            return self.mac
      
      
