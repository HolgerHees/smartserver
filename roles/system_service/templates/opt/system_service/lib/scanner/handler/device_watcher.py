import threading
import socket
import traceback

from datetime import datetime, timedelta
import time
import logging

from lib.scanner.handler import _handler

from lib.scanner.dto.device import Device
from lib.scanner.dto.event import Event

from lib.scanner.helper import Helper

class AddressHelper():
    def knock(address_family,ip_address):
        s = socket.socket(address_family, socket.SOCK_DGRAM)
        s.setblocking(False)
        socket_address = (ip_address, 5353)
        s.sendto(b'', socket_address)
        s.close()
        
    def getAddressFamily(ip_address):
        address_family, _, _, _, (ip_address, _) = socket.getaddrinfo(
            host=ip_address,
            port=None,
            flags=socket.AI_ADDRCONFIG
        )[0]
        return address_family

class DeviceWatcherJob(threading.Thread):
    '''Device client'''
    def __init__(self, handler, cache, device, stat, interface, type, timeout):
        threading.Thread.__init__(self) 
        
        self.is_running = True
        self.event = threading.Event()
        self.lock = threading.Lock()

        self.handler = handler
        self.cache = cache
        self.device = device
        self.stat = stat
        self.interface = interface

        self.type = type

        self.timeout = timeout

        self.force = False
        self.wakeup_reasons = []

    def _isRunning(self):
        return self.is_running
      
    def run(self):
        logging.info("Device watcher for {} started".format(self.device))
        is_supended = False
        
        while self._isRunning():
            try:
                if is_supended:
                    logging.warning("Resume device watcher")
                    is_supended = False

                while self._isRunning():
                    with self.lock:
                        if len(self.wakeup_reasons) > 0:
                            reason = ", Wakeup: {}".format(", ".join(self.wakeup_reasons))
                            self.wakeup_reasons = []
                        else:
                            reason = ""

                        if self.force:
                            logging.info(">>> Device: {}, Step: FORCE{}".format(self.device, reason))
                            break

                        # online devices waiting time = 60 + 5 seconds
                        if self.stat.isOnline():
                            last_seen = (datetime.now() - self.stat.getValidatedLastSeen()).total_seconds()
                            diff = 65 - last_seen # use 65 seconds instead of 60 seconds, to have some overlapping with interval timeouts from e.g. openwrt collector. They will maybe change 'validatedLastSeen'
                            if diff <= 0:
                                logging.info(">>> Device: {}, Step: BREAK{}".format(self.device, reason))
                                break

                            logging.info(">>> Device: {}, Step: SLEEP {:.2f}{}".format(self.device, diff, reason))
                            sleeptime = diff
                        # offline devices waiting time = 300 seconds
                        else:
                            logging.info(">>> Device: {}, Step: SLEEP forever{}".format(self.device, reason))
                            sleeptime = -1

                        self.event.clear()

                    if sleeptime == -1:
                        self.event.wait()
                    else:
                        self.event.wait(sleeptime)

                arp_timeout = 10
                ping_timeout = 10

                if self.stat.isOnline():
                    total_timeout = self.timeout
                else:
                    # non android devices neededs more retries because of for multiple calls of 'knock' during offline check time
                    total_timeout = ( 1 if self.type == "android" else 3 ) * ( arp_timeout + ping_timeout )

                start_time = datetime.now()
                ip_address = self.device.getIP()
                validated_last_seen = self.stat.getValidatedLastSeen()
                while self._isRunning():
                    if self.type != "android":
                        AddressHelper.knock(AddressHelper.getAddressFamily(ip_address), ip_address)
                        time.sleep(0.05)

                    methods = ["arping"]
                    answering_mac = Helper.getMacFromArpPing(ip_address, self.interface, arp_timeout, self._isRunning)
                    if answering_mac is None:
                        methods.append("ping")
                        answering_mac = Helper.getMacFromPing(ip_address, ping_timeout, self._isRunning)

                    duration = round((datetime.now() - start_time).total_seconds(),2)

                    if answering_mac is not None:
                        if answering_mac != self.device.getMAC():
                            logging.info("Device {} has wrong ip. Answering MAC was {} after {} seconds".format(self.device, answering_mac, duration))
                            self.cache.lock(self)
                            self.device.lock(self)
                            self.device.clearIP()
                            self.cache.confirmDevice( self.handler, self.device )
                            self.stat.lock(self)
                            self.stat.setOffline()
                            self.cache.confirmStat( self.handler, self.stat )
                            self.cache.unlock(self)

                            self.is_running = False
                            self.handler._cleanupJob(self.device)
                        else:
                            logging.info("Device {} is online. Checked with {} in {} seconds".format(self.device, " & ".join(methods), duration))
                            self.cache.lock(self)
                            self.stat.lock(self)
                            self.stat.setLastSeen(True)
                            self.cache.confirmStat( self.handler, self.stat )
                            self.cache.unlock(self)
                        break

                    if validated_last_seen != self.stat.getValidatedLastSeen():
                        break

                    if duration >= total_timeout:
                        logging.info("Device {} is offline. Checked with {} in {} seconds".format(self.device," & ".join(methods), duration))
                        self.cache.lock(self)
                        self.stat.lock(self)
                        self.stat.setOffline()
                        self.cache.confirmStat( self.handler, self.stat )
                        self.cache.unlock(self)
                        break

            except Exception as e:
                self.cache.cleanLocks(self)
                logging.error("Device watcher got unexpected exception. Will suspend for 15 minutes.")
                logging.error(traceback.format_exc())
                is_supended = True
                    
            if is_supended:
                self.event.wait(900)
                self.event.clear()

            with self.lock:
                self.force = False
                self.wakeup_reasons = []

        logging.info("Device watcher for {} stopped".format(self.device))

    def wakeup(self, reason, force):
        with self.lock:
            self.wakeup_reasons.append(reason)
            if force:
                self.force = True
            self.event.set()

    def terminate(self):
        self.is_running = False
        self.event.set()
        self.join()

class DeviceWatcher(_handler.Handler):
    def __init__(self, config, cache ):
        super().__init__(config,cache)
        
        self.lock = threading.Lock()
        self.jobs = {}

    def start(self):
        super().start()

    def terminate(self):
        with self.lock:
            for mac in self.jobs:
                self.jobs[mac].terminate()
        super().terminate()

    def _run(self):
        while self._isRunning():
            self._wait(900)

    def _cleanupJob(self, device):
        with self.lock:
            mac = device.getMAC()
            del self.jobs[mac]

    def getEventTypes(self):
        return [ 
            { "types": [Event.TYPE_DEVICE], "actions": [Event.ACTION_CREATE,Event.ACTION_MODIFY], "details": ["ip","connection"] },
            { "types": [Event.TYPE_DEVICE_STAT], "actions": None, "details": ["online_state"] }
        ]

    def processEvents(self, events):
        for event in events:
            mac = event.getObject().getMAC()

            if event.getType() == Event.TYPE_DEVICE:
                device = event.getObject()

                if event.hasDetail("ip"):
                    with self.lock:
                        if device.getIP() in self.config.user_devices and mac not in self.jobs:
                            stat = self.cache.getUnlockedDeviceStat(mac)
                            if stat is None:
                                self.cache.lock(self)
                                stat = self.cache.getDeviceStat(mac) # force creation if device stat
                                stat.unlock(self)
                                self.cache.unlock(self)

                            user_config = self.config.user_devices[device.getIP()]
                            self.jobs[mac] = DeviceWatcherJob(self, self.cache, device, stat, self.config.main_interface, user_config["type"], user_config["timeout"])
                            self.jobs[mac].start()
                    continue

                if device.getIP() not in self.config.user_devices:
                    continue

                if event.hasDetail("connection"):
                    job = self.jobs.get(mac, None)
                    if job is None:
                        continue

                    stat = self.cache.getUnlockedDeviceStat(mac)
                    is_online = stat is not None and stat.isOnline()

                    detail = event.getDetail("connection")
                    if Device.EVENT_DETAIL_CONNECTION_DISABLE in detail:
                        if is_online:
                            job.wakeup("connection disabled", True)
                    elif Device.EVENT_DETAIL_CONNECTION_ENABLE in detail:
                        if not is_online:
                            job.wakeup("connection enabled", True)
                    continue
            else:
                device = self.cache.getUnlockedDevice(mac)

                if device.getIP() not in self.config.user_devices:
                    continue

                if event.hasDetail("online_state"):
                    job = self.jobs.get(mac, None)
                    if job is None:
                        continue

                    job.wakeup("changed online state", False)
                    continue
