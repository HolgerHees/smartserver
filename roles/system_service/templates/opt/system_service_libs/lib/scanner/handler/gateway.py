import logging
import threading

from lib.scanner.handler import _handler
from lib.scanner.dto._changeable import Changeable
from lib.scanner.dto.device import Device, Connection
from lib.scanner.dto.event import Event
from lib.scanner.helper import Helper


class Gateway(_handler.Handler): 
    def __init__(self, config, cache ):
        super().__init__(config,cache,False)
                
    def getEventTypes(self):
        return [ { "types": [Event.TYPE_DEVICE], "actions": [Event.ACTION_CREATE], "details": None } ]

    def processEvents(self, events):
        try:
            self.cache.lock(self)
            for event in events:
                gateway_mac = self.cache.getGatewayMAC()
                vlan = self.config.default_vlan

                device = event.getObject()
                device.lock(self)
                if gateway_mac == device.getMAC():
                    device.setType("gateway", 100, "network")
                    device.addHopConnection(Connection.ETHERNET, self.cache.getWanMAC(), self.cache.getWanInterface() )
                else:
                    device.addHopConnection(Connection.ETHERNET, gateway_mac, self.cache.getGatewayInterface(vlan), { "vlan": vlan } )
                
                self.cache.confirmDevice( self, device )
                
            self.cache.unlock(self)
        except Exception as e:
            self.cache.cleanLocks(self)
            self._handleUnexpectedException(e, None, -1)
