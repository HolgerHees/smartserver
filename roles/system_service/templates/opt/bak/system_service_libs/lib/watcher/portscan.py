import threading
from datetime import datetime, timedelta
import re
from collections import deque

from smartserver import command

from lib.watcher import watcher

class PortScanner(watcher.Watcher): 
    def __init__(self, logger, config, handler ):
        super().__init__(logger)
      
        self.logger = logger
        self.config = config
        self.handler = handler
        
        self.is_running = True
        self.last_refresh = 0
        
        self.queue_lock = threading.Lock()
        self.waiting_queue = deque()
        self.running_queue = deque()
        
        self.processed_ips = 0

        self.port_map_lock = threading.Lock()
        self.port_map = {}
        self.port_last_check = {}
        
        self.condition = threading.Condition()
        self.thread = threading.Thread(target=self.checkPortMap, args=())
        
    def start(self):
        pass
        #self.thread.start()
        
    def terminate(self):
        with self.condition:
            self.is_running = False
            self.condition.notifyAll()

    def notify(self, changes):
        if "ports" not in changes:
            return
        
        now = datetime.now()
        is_changed = False
        with self.queue_lock:
            known_ips = {};#FIXME self.arp_scanner.getKnownIps()
            for ip in known_ips:
                if ip not in self.port_map and ip not in self.waiting_queue and ip not in self.running_queue:
                    self.logger.info("Add ip '{}'".format(ip))
                    self.waiting_queue.append(ip)
                    is_changed = True
                #elif (now - self.port_last_check[ip]).total_seconds() > 60 * 60 * 24:
                #    self.waiting_queue.append(ip)
                
            with self.port_map_lock:
                for ip in list(self.port_map.keys()):
                    
                    if ip not in known_ips:
                        self.logger.info("Clean ip '{}'".format(ip))
                        del self.port_map[ip]
                        del self.port_last_check[ip]
              
        if is_changed:
            with self.condition:
                self.condition.notifyAll()
        
    def checkPortMap(self):
        while self.is_running:
            with self.queue_lock:
                while self.is_running and len(self.waiting_queue) > 0 and len(self.running_queue) <= 5:
                    ip = self.waiting_queue.popleft()
                    self.running_queue.append(ip)
                    self.processed_ips += 1
                    t = threading.Thread(target = self._checkPorts, args = [ ip ] )
                    t.start()
                    
                #self.logger.info("waiting: {}, running: {}, processed: {}".format(len(self.waiting_queue), len(self.running_queue), self.processed_ips))
                #self.logger.info(self.running_queue)
                
                if self.is_running and len(self.waiting_queue) == 0 and len(self.running_queue) == 0 and self.processed_ips > 0:
                    self.handler.notify(["scanned_ports"])
                    
                with self.port_map_lock:
                    now = datetime.now()
                    for ip in self.port_last_check:
                        if (now - self.port_last_check[ip]).total_seconds() > self.config.port_rescan_interval:
                            self.running_queue.append(ip)
                            self.processed_ips += 1
                            t = threading.Thread(target = self._checkPorts, args = [ ip ] )
                            t.start()
                    
            if self.is_running:
                with self.condition:
                    self.condition.wait(self.config.port_scan_interval)
            
    def _checkPorts(self, ip):
        self.logger.info("Start portscan for '{}'".format(ip))
        
        result = command.exec(["/usr/bin/nmap", "-sS", ip])
        rows = result.stdout.decode().strip().split("\n")

        ports = []

        for row in rows:
            match = re.match("([0-9]*)/([a-z]*)\s*([a-z]*)\s*(.*)",row)
            if not match:
                continue
        
            ports.append({"port": match[1], "type": match[2], "state": match[3], "service": match[4] })
                
        with self.port_map_lock:
            self.port_last_check[ip] = datetime.now()
            self.port_map[ip] = ports
        
        with self.queue_lock:
            self.running_queue.remove(ip)
                
        with self.condition:
            self.condition.notifyAll()
            
    def processDevices(self, devices, groups):
        for device in devices:
            if device.getIp() in self.port_map:
                 port = port_map[device.getIp()]
                 device.appendService(port["port"], port["service"])
