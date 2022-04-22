import logging
import threading

from lib.handler import _handler
from lib.dto._changeable import Changeable
from lib.dto.device import Device, Connection
from lib.dto.stat import Stat
from lib.dto.event import Event
from lib.helper import Helper


class Gateway(_handler.Handler): 
    def __init__(self, config, cache ):
        super().__init__()
      
        self.config = config
        self.cache = cache
                
    def getEventTypes(self):
        return [ { "types": [Event.TYPE_DEVICE], "actions": [Event.ACTION_CREATE,Event.ACTION_MODIFY], "details": ["connection"] } ]

    def processEvents(self, events):
        _events = []
        
        self.cache.lock()
        for event in events:
            device = event.getObject()
            gateway_mac = self.cache.getGatewayMAC()
            
            if gateway_mac != device.getMAC():
                _connection = device.getConnection()
                if _connection is not None:
                    for vlan in _connection.getVLANs():
                        event.getObject().addHopConnection(Connection.VIRTUAL, vlan, gateway_mac, "lan{}".format(vlan) );
                    self.cache.confirmDevice( device, lambda event: events.append(event) )
        self.cache.unlock()
            
        if len(_events) > 0:
            self.getDispatcher().notify(_events)
