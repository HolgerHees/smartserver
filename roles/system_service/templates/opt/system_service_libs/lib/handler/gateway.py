import logging

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
        
        self.gateway_mac = None
    
    def getEventTypes(self):
        return [ { "types": [Event.TYPE_DEVICE], "actions": [Event.ACTION_CREATE], "details": None } ]

    def processEvents(self, events):
        if self.gateway_mac is None:
            self.gateway_mac = self.cache.ip2mac(self.config.default_gateway_ip)
            if self.gateway_mac is None:
                logging.warning("Default gateway '{}' currently not resolvable.".format(self.config.default_gateway_ip))
                return
        
        _events = []
        
        self.cache.lock()
        for event in events:
            device = event.getObject()
            
            if device.getMAC() == self.gateway_mac:
                for _device in self.cache.getDevices():
                    if _device.getMAC() == self.gateway_mac:
                        continue
                    
                    _device.addHopConnection(Connection.VIRTUAL, self.config.default_vlan, self.gateway_mac, "lan0" );
                    self.cache.confirmDevice( _device, lambda event: events.append(event) )
            else:
                event.getObject().addHopConnection(Connection.VIRTUAL, self.config.default_vlan, self.gateway_mac, "lan0" );
                self.cache.confirmDevice( device, lambda event: events.append(event) )
        self.cache.unlock()
            
        if len(_events) > 0:
            self.getDispatcher().notify(_events)
