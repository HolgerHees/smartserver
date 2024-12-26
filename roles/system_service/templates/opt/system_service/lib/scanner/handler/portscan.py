import threading
from datetime import datetime, timedelta
import re
from collections import deque
import logging
import time
import random
import schedule
import os

from smartserver import command
from smartserver.confighelper import ConfigHelper
from smartserver.metric import Metric

from lib.scanner.handler import _handler
from lib.scanner.helper import Helper
from lib.scanner.dto.event import Event


class PortScanner(_handler.Handler): 
    def __init__(self, config, cache ):
        super().__init__(config,cache)
        
        self.last_refresh = 0

        self.max_running_queue_length = 5
        
        self.queue_lock = threading.Lock()
        self.waiting_queue = deque()
        self.running_queue = deque()
        
        self.data_lock = threading.Lock()
        self.monitored_devices = {}

        self.registered_devices = {}

        self.dump_path = "/var/lib/system_service/port_scanner.json"
        self.valid_cache_file = True
        self.version = 1

        self.started_at = time.time()

    def getStateMetrics(self):
        metrics = super().getStateMetrics()
        metrics.append(Metric.buildStateMetric("system_service", "scanner.handler.portscan", "cache_file", "1" if self.valid_cache_file else "0"))
        return metrics

    def start(self):
        schedule.every().day.at("01:00").do(self._dump)
        schedule.every().hour.at("00:00").do(self._cleanup)
        self._restore()

        super().start()

    def terminate(self):
        if self._isRunning() and os.path.exists(self.dump_path):
            self._dump()

        super().terminate()
        
    def _restore(self):
        self.valid_cache_file, data = ConfigHelper.loadConfig(self.dump_path, self.version )
        if data is not None:
            self.monitored_devices = data["monitored_devices"]
            logging.info("Loaded {} devices".format(len(self.monitored_devices)))
        else:
            self.monitored_devices = {}
            self._dump()

    def _dump(self):
        if self.valid_cache_file:
            with self.data_lock:
                ConfigHelper.saveConfig(self.dump_path, self.version, { "monitored_devices": self.monitored_devices } )
                logging.info("Saved {} devices".format(len(self.monitored_devices)))

    def _cleanup(self):
        # Skip cleanup during first hour. Need more time to detect devices.
        if time.time() - self.started_at < 60 * 60:
            return

        device_count = 0
        with self.data_lock:
            for _mac in list(self.monitored_devices.keys()):
                device = self.cache.getUnlockedDevice(_mac)
                if device is None:
                    del self.monitored_devices[_mac]
                    device_count += 1
        if device_count > 0:
            logging.info("Cleaned {} devices".format(device_count))

    def _run(self):
        if not os.path.exists(self.dump_path):
            self._dump()

        _last_size = { "total": -1, "waiting": -1, "running": -1 }
        while self._isRunning():
            _queues_changed = _last_size["total"] != len(self.monitored_devices) or _last_size["waiting"] != len(self.waiting_queue) or _last_size["running"] != len(self.running_queue)

            if not self._isSuspended():
                try:
                    timeout = self.config.port_scan_interval

                    with self.queue_lock:
                        while self._isRunning() and len(self.waiting_queue) > 0 and len(self.running_queue) < self.max_running_queue_length:
                            device = self.waiting_queue.popleft()
                            if device.getMAC() not in self.monitored_devices:
                                continue
                            self.running_queue.append(device)
                            t = threading.Thread(target = self._checkPorts, args = [ device ] )
                            t.start()
                            _queues_changed = True

                        now = time.time()
                        for mac in self.monitored_devices:
                            device = self.cache.getUnlockedDevice(mac)
                            if device is None or device.getIP() is None or device in self.waiting_queue or device in self.running_queue:
                                continue

                            if now >= self.monitored_devices[mac]["time"]:
                                self.waiting_queue.append(device)
                                _timeout = self.config.port_rescan_interval
                            else:
                                _timeout = self.monitored_devices[mac]["time"] - now

                            if _timeout < timeout:
                                timeout = _timeout

                        if len(self.running_queue) < self.max_running_queue_length and len(self.waiting_queue) > 0:
                            timeout = 0

                except Exception as e:
                    self._handleUnexpectedException(e)

            suspend_timeout = self._getSuspendTimeout()
            if self._isRunning() and suspend_timeout > 0:
                timeout = suspend_timeout

            if timeout > 0:
                if _queues_changed:
                    _last_size["total"] = len(self.monitored_devices)
                    _last_size["waiting"] = len(self.waiting_queue)
                    _last_size["running"] = len(self.running_queue)
                    logging.info("Queue statistic - TOTAL: {}, WAITING: {}, RUNNING: {}".format(len(self.monitored_devices), len(self.waiting_queue), len(self.running_queue)))
                self._wait(timeout)
            else:
                if _queues_changed:
                    _last_size = { "total": -1, "waiting": -1, "running": -1 }

    def _checkPorts(self, device):
        _start = time.time()
        services = Helper.nmap(device.getIP(), self._isRunning) if device.getMAC() not in self.config.silent_device_macs else {}
        _end = time.time()
        logging.info("Scanning device {} done after {} seconds".format(device.getIP(), round(_end-_start,0)))

        if self._isRunning() and device.getMAC() in self.monitored_devices:
            with self.data_lock:
                # randomize next scan to avoid flooting connection track table of netfilter
                self.monitored_devices[device.getMAC()]["time"] = time.time() + self.config.port_rescan_interval + random.randint(0,3600)
                self.monitored_devices[device.getMAC()]["services"] = services

                self._setServices(device, services)

        with self.queue_lock:
            self.running_queue.remove(device)
                
        self._wakeup()

    def _setServices(self, device, services):
        if len(device.getServices()) != len(services) or device.getServices() != services:
            self.cache.lock(self)
            device.lock(self)
            device.setServices(services)
            self.cache.confirmDevice( self, device )
            self.cache.unlock(self)

    def getEventTypes(self):
        return [ 
            { "types": [Event.TYPE_DEVICE], "actions": [Event.ACTION_DELETE], "details": None },
            { "types": [Event.TYPE_DEVICE], "actions": None, "details": ["ip"] }
        ]

    def processEvents(self, events):
        with self.data_lock:
            has_changed_devices = False
            for event in events:
                mac = event.getObject().getMAC()
                if event.getAction() == Event.ACTION_DELETE:
                    # device exists only if it has an IP, Otherwise it was never added.
                    if mac in self.monitored_devices or mac in self.registered_devices:
                        logging.info("Remove device {}".format(event.getObject()))
                        if mac in self.monitored_devices:
                            del self.monitored_devices[mac]
                        if mac in self.registered_devices:
                            del self.registered_devices[mac]
                else:
                    if mac not in self.monitored_devices:
                        logging.info("Add device {}".format(event.getObject()))
                        self.monitored_devices[mac] = { "time": time.time(), "services": {} }
                        self.registered_devices[mac] = True
                    else:
                        if mac not in self.registered_devices:
                            logging.info("Restore device {}".format(event.getObject()))
                            self.registered_devices[mac] = True

                            device = self.cache.getUnlockedDevice(mac)
                            self._setServices(device, self.monitored_devices[mac]["services"])
                        else:
                            logging.info("Change device {}".format(event.getObject()))
                            self.monitored_devices[mac]["time"] = time.time() + random.randint(0,300)

                    has_changed_devices = True

            if has_changed_devices:
                self._wakeup()
