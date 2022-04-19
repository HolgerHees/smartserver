from lib.handler import _handler
from lib.dto._changeable import Changeable
from lib.dto.device import Device, Connection
from lib.dto.stat import Stat
from lib.dto.event import Event
from lib.helper import Helper


class DefaultGateway(_handler.Handler): 
    def __init__(self, config, cache ):
        super().__init__()
      
        self.config = config
        self.cache = cache
    
    def getEventTypes(self):
        return [ { "types": [Event.TYPE_DEVICE], "actions": [Event.ACTION_CREATE], "details": None } ]

    def processEvents(self, events):
        vlan = self.config.default_vlan
        target_mac = self.cache.ip2mac(self.config.default_gateway_ip)
        target_interface = "lan0"

        _events = []
        for event in events:
            device = event.getObject()
            
            self.cache.lock()
            event.getObject().addHopConnection(Connection.ETHERNET, vlan, target_mac, target_interface );
            self.cache.confirmDevice( device, lambda event: events.append(event) )
            self.cache.unlock()
            
        if len(_events) > 0:
            self.getDispatcher().notify(_events)
