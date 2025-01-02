import logging

from lib.scanner.dto._changeable import Changeable
from lib.scanner.dto.event import Event


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
        return "type: {}, mac: {}, interface: {}".format(self.type,self.target_mac,self.target_interface)
    
class Device(Changeable):
    EVENT_DETAIL_CONNECTION_ADD = "add"
    EVENT_DETAIL_CONNECTION_ENABLE = "enable"
    EVENT_DETAIL_CONNECTION_REMOVE = "remove"
    EVENT_DETAIL_CONNECTION_DISABLE = "disable"

    def __init__(self, cache, mac, type):
        super().__init__(cache)

        self.mac = mac
        
        self.info = None
        
        self.hop_connection_map = {}
        self.multi_connections = False
        self.connection = None
        self.connection_state = 0

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

    def clearIP(self):
        self._checkLock()
        self._clearPriorizedData("ip")

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
            return True
        return False

    def addHopConnection(self, type, target_mac, target_interface, details = None ):
        self._checkLock()
        #if target_mac == self.cache.getGatewayMAC():
        #    _connections = list(filter(lambda c: c.getTargetMAC() == target_mac, self.hop_connections ))
        #    if len(_connections) > 0:
        #        if _connections[0].getType() != Connection.ETHERNET:
        #            return
        #        else:
        #            self.hop_connections.remove(_connections[0])

        key = "{}:{}".format(target_mac,target_interface)
        
        action = None

        if key in self.hop_connection_map:
            _connection = self.hop_connection_map[key]

            if _connection.getType() != type:
                raise Exception("Wrong connection type")
            
            if details is not None and not _connection.hasDetails(details):
                _connection.addDetails(details)
                action = Device.EVENT_DETAIL_CONNECTION_ADD

            if not _connection.isEnabled():
                _connection.setEnabled(True)
                action = Device.EVENT_DETAIL_CONNECTION_ENABLE
        else:
            if type == Connection.WIFI:
                self.supports_wifi = True
                
            self.hop_connection_map[key] = Connection(type, target_mac, target_interface, [ details ] if details is not None else [] )
            action = Device.EVENT_DETAIL_CONNECTION_ADD
            
        if action is None:
            return

        target_device = self.cache.getUnlockedDevice(target_mac)
        self._markAsChanged("connection", "{} connection to {}:{}".format(action, target_device if target_device else target_mac, details), action)

        # *** CLEANUP only needed for added connections and NOT for enabled or unchanged ones ***
        if action == Device.EVENT_DETAIL_CONNECTION_ADD:
            _connections = list(filter(lambda c: c.getType() == type and not c.isEnabled(), self.hop_connection_map.values() ))
            for _connection in _connections:
                target_mac = _connection.getTargetMAC()
                target_device = self.cache.getUnlockedDevice(target_mac)
                key = "{}:{}".format(target_mac,_connection.getTargetInterface())
                del self.hop_connection_map[key]
                self._markAsChanged("connection", "remove disabled connection to {}:{}".format(target_device if target_device else target_mac, _connection.getDetailsList() ), Device.EVENT_DETAIL_CONNECTION_REMOVE)

    def removeHopConnection(self, type, target_mac, target_interface, details, disable_last_of_type = False):
        self._checkLock()

        key = "{}:{}".format(target_mac,target_interface)

        if key in self.hop_connection_map:
            _connection = self.hop_connection_map[key]

            action = Device.EVENT_DETAIL_CONNECTION_REMOVE

            if _connection.hasDetails(details):
                if len(_connection.getDetailsList()) == 1:
                    if disable_last_of_type and len(list(filter(lambda c: c.getType() == type, self.hop_connection_map.values() ))) == 1:
                        _connection.setEnabled(False)
                        action = Device.EVENT_DETAIL_CONNECTION_DISABLE
                    else:
                        del self.hop_connection_map[key]
                else:
                    _connection.removeDetails(details)

            target_device = self.cache.getUnlockedDevice(target_mac)
            self._markAsChanged("connection", "{} connection from {}:{}".format(action, target_device if target_device else target_mac, details), action)

    def getHopConnections(self):
        return list(self.hop_connection_map.values())

    def setVirtualConnection(self, connection):
        self.virtual_connection = connection
        
    def getConnection(self):
        return self.virtual_connection if self.virtual_connection is not None else self.connection
   
    def hasMultiConnections(self):
        return self.multi_connections
        
    def generateMultiConnectionEvents(self, event, events):
        if not event.hasDetail("signal"):
            return
        
        found = False
        for event in events:
            if event.getType() == self.getEventType() and event.getObject() == self and event.hasDetail("connection"):
                found = True
        
        if not found:
            events.append(Event(self.getEventType(), Event.ACTION_MODIFY, self, ["connection", "connection_helper"]))
        
    def calculateConnectionPath(self, _backward_interfaces):
        #logging.info("CALCULATE")

        multi_connections = False

        if self.getMAC() == self._getCache().getGatewayMAC():
            connection = self.getHopConnections()[0]
            connection_state = 0
        else:
            connection = None
            connection_state = 3

            for _connection in self.getHopConnections():
                if _connection.getType() == Connection.WIFI:
                    if connection is None:
                        connection = _connection
                        connection_state = 0
                    else:
                        max_signal = -256
                        stat = self.cache.getUnlockedConnectionStat(connection.getTargetMAC(),connection.getTargetInterface())
                        for stat_data in stat.getDataList():
                            signal = int(stat_data.getDetail("signal","-256"))
                            if signal > max_signal:
                                max_signal = signal

                        _max_signal = -256
                        _stat = self.cache.getUnlockedConnectionStat(_connection.getTargetMAC(),_connection.getTargetInterface())
                        for _stat_data in _stat.getDataList():
                            _signal = int(_stat_data.getDetail("signal","-256"))
                            if _signal > _max_signal:
                                _max_signal = _signal

                        if _max_signal > max_signal:
                            connection = _connection

                        multi_connections = True

            if connection is None:
                _tmp_connections = {}
                _hob_connections = {}

                for _connection in self.getHopConnections():
                    _key = "{}:{}".format(_connection.getTargetMAC(),_connection.getTargetInterface())
                    if _key in _backward_interfaces:
                        continue
                    _tmp_connections[_key] = _connection

                    _target_device = self.cache.getUnlockedDevice(_connection.getTargetMAC())
                    if _target_device is None:
                        continue

                    for __connection in _target_device.getHopConnections():
                        __key = "{}:{}".format(__connection.getTargetMAC(),__connection.getTargetInterface())
                        if __key in _backward_interfaces:
                            continue
                        _hob_connections[__key] = True

                _filtered_connections = {k: v for k, v in _tmp_connections.items() if k not in _hob_connections}

                if len(_filtered_connections.keys()) == 1:
                    #logging.info("OK " + self.getIP())
                    connection = list(_filtered_connections.values())[0]
                    connection_state = 0
                elif len(_filtered_connections.keys()) > 1:
                    connection = list(_filtered_connections.values())[0]
                    connection_state = 1
                    #logging.info("Not able to detect filtered network route of " + str(self) + " " + str(_filtered_connections.keys()) + " => " + str(connection))
                elif len(_tmp_connections) > 0:
                    connection = list(_tmp_connections.values())[0]
                    connection_state = 2
                    #logging.info("Not able to detect unfiltered network route of " + str(self) + " " + str(_tmp_connections.keys()) + " => " + str(connection))
                else:
                    logging.error("Not able to detect any network route of " + str(self))

        if connection != self.connection:
            self.multi_connections = multi_connections
            self.connection = connection
            self.connection_state = connection_state
            return True

        return True

    def supportsWifi(self):
        return self.supports_wifi

    def setServices(self, services):
        self._checkLock()
        self._markAsChanged("services")
        self.services = services

    def getServices(self):
        return self.services

    def getSerializeable(self, config ):
        connection = self.getConnection()

        return {
            "mac": self.mac,

            "type": self.getType(),
            "ip": self.getIP(),
            "dns": self.getDNS(),
            
            "info": self.info,

            "silent": 1 if self.mac in config.silent_device_macs else 0,
            
            "connection": connection.getSerializeable() if connection else None,
            "connection_state": self.connection_state,

            "services": self.services,
            "details": self._getDetails()
        }
    
    def __repr__(self):
        ip = self.getIP()
        if ip:
            return ip
        else:
            return self.mac
      
      
