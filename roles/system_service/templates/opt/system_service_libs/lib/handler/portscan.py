import threading
from datetime import datetime, timedelta
import re
from collections import deque
import logging

from smartserver import command

from lib.handler import _handler
from lib.helper import Helper
from lib.dto.event import Event


class PortScanner(_handler.Handler): 
    def __init__(self, config, cache ):
        super().__init__()
      
        self.config = config
        self.cache = cache
        
        self.is_running = True
        self.last_refresh = 0
        
        self.queue_lock = threading.Lock()
        self.waiting_queue = deque()
        self.running_queue = deque()
        
        self.data_lock = threading.Lock()
        self.monitored_devices = {}
        
        self.condition = threading.Condition()
        self.thread = threading.Thread(target=self.checkPortMap, args=())
        
    def start(self):
        self.thread.start()
        
    def terminate(self):
        with self.condition:
            self.is_running = False
            self.condition.notifyAll()

    def checkPortMap(self):
        while self.is_running:
            with self.queue_lock:               
                while self.is_running and len(self.waiting_queue) > 0 and len(self.running_queue) <= 5:
                    device = self.waiting_queue.popleft()
                    self.running_queue.append(device)
                    t = threading.Thread(target = self._checkPorts, args = [ device ] )
                    t.start()
                    
                now = datetime.now()
                next_timeout = self.config.port_scan_interval
                for mac in self.monitored_devices:
                    device = self.cache.getUnlockedDevice(mac)
                    if device.getIP() is None or device in self.waiting_queue or device in self.running_queue:
                        continue
                    
                    if self.monitored_devices[mac] == None or (now - self.monitored_devices[mac]).total_seconds() > self.config.port_rescan_interval:
                        self.waiting_queue.append(device)
                        _timeout = self.config.port_rescan_interval
                    elif self.monitored_devices[mac] != None:
                        _timeout = (now - self.monitored_devices[mac]).total_seconds()
                        
                    if _timeout < next_timeout:
                        next_timeout = _timeout
                    
            if self.is_running:
                with self.condition:
                    self.condition.wait(next_timeout)
            
    def _checkPorts(self, device):
        services = Helper.nmap(device.getIP())
                
        with self.data_lock:
            self.monitored_devices[device.getMAC()] = datetime.now()

            self.cache.lock()
            events = []
            device.setServices(services)
            self.cache.confirmDevice( device, lambda event: events.append(event) )
            self.cache.unlock()

            if len(events) > 0:
                self._getDispatcher().dispatch(self,events)

        with self.queue_lock:
            self.running_queue.remove(device)
                
        with self.condition:
            self.condition.notifyAll()
            
    def getEventTypes(self):
        return [ 
            { "types": [Event.TYPE_DEVICE], "actions": [Event.ACTION_DELETE], "details": None },
            { "types": [Event.TYPE_DEVICE], "actions": None, "details": ["ip"] } 
        ]

    def processEvents(self, events):
        with self.data_lock:
            for event in events:
                mac = event.getObject().getMAC()
                if event.getAction() == Event.ACTION_DELETE:
                    logging.info("Remove device {}".format(event.getObject()))
                    del self.monitored_devices[mac]
                else:
                    if mac not in self.monitored_devices:
                        logging.info("Add device {}".format(event.getObject()))
                    else:
                        logging.info("Change device {}".format(event.getObject()))
                        
                    self.monitored_devices[mac] = None

        with self.condition:
            self.condition.notifyAll()
