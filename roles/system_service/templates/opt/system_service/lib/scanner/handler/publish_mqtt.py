from datetime import datetime
import time

from lib.scanner.handler import _handler
from lib.scanner.dto.device_stat import DeviceStat
from lib.scanner.dto.event import Event
from lib.scanner.helper import Helper


class MQTTPublisher(_handler.Handler): 
    def __init__(self, config, cache, mqtt ):
        super().__init__(config,cache)
        
        self.skipped_macs = {}
        self.allowed_details = {}
        
        self.mqtt = mqtt
        
        self.published_values = {}

    def start(self):
        super().start()

    def terminate(self):
        super().terminate()
        
    def _run(self):
        while self._isRunning():
            if not self._isSuspended():
                try:
                    now = datetime.now()
                    timeout = self.config.mqtt_republish_interval
                    
                    for mac in list(self.published_values.keys()):
                        _device = self.cache.getUnlockedDevice(mac)
                        if _device is None or _device.getIP() != self.published_values[mac]['ip']:
                            Helper.logInfo("CLEAN values of mac: {}, device: {}, published: {}".format(mac, device, self.published_values[mac] ))
                            del self.published_values[mac]
                            continue
                        
                        _to_publish = {}
                        for [detail, topic, value, last_publish] in self.published_values[mac]['values'].values():
                            
                            _diff = (now-last_publish).total_seconds()
                            if _diff >= self.config.mqtt_republish_interval:
                                _to_publish[detail] = [detail, topic, value]
                            else:
                                _timeout = self.config.mqtt_republish_interval - _diff
                                if _timeout < timeout:
                                    timeout = _timeout
                                    
                        if len(_to_publish) > 0:
                            _msg = []
                            for detail,topic,value in _to_publish.values():
                                _msg.append("{} => {}".format(detail,value))
                            Helper.logInfo("REPUBLISH {} of {}".format(_msg, _device))

                            for [detail, topic, value] in _to_publish.values():
                                self._publishValue(mac, _device.getIP(), detail, topic, value, now)
                except Exception as e:
                    self._handleUnexpectedException(e)

            suspend_timeout = self._getSuspendTimeout()
            if suspend_timeout > 0:
                timeout = suspend_timeout

            self._wait(timeout)

    def _publishValues(self, device, stat, changed_details = None):
        mac = device.getMAC()
        ip = device.getIP()

        if ip is None:
            self.skipped_macs[mac] = True
            return

        allowed_details = ["wan_type","wan_state"]
        if ip in self.config.user_devices:
            allowed_details.append("online_state")
        
        _details = []
        if changed_details is None:
            _details = allowed_details
        else:
            for detail in changed_details:
                if detail not in allowed_details:
                    continue
                _details.append(detail)
                
        if len(_details) == 0:
            return

        _to_publish = {}
        if type(stat) is DeviceStat:
            for detail in _details:
                if detail == "online_state":
                    topic = "network/{}/{}".format(device.getIP(),"online")
                    value = "ON" if stat.isOnline() else "OFF"
                    _to_publish[detail] = [detail,topic,value]
        else:
            for detail in _details:
                for data in stat.getDataList():
                    if detail in ["wan_type","wan_state"] and data.getDetail(detail) is not None:
                        topic = "network/{}/{}".format(device.getIP(),detail)
                        _to_publish[detail] = [detail,topic,data.getDetail(detail)]
                
        if len(_to_publish.values()) == 0:
            return

        _msg = []
        for detail,topic,value in _to_publish.values():
            _msg.append("{} => {}".format(detail,value))
        Helper.logInfo("PUBLISH {} of {}".format(_msg, device))

        now = datetime.now()
        for [detail, topic, value] in _to_publish.values():
            self._publishValue(mac, ip, detail, topic, value, now)
                
        self._wakeup()

        if mac in self.skipped_macs:
            del self.skipped_macs[mac]
    
    def _publishValue(self, mac, ip, detail, topic, value, now):
        if mac not in self.published_values:
            self.published_values[mac] = { 'ip': ip, 'values': {} }
            
        self.mqtt.publish(topic, value )
        self.published_values[mac]['values'][topic] = [detail, topic, value, now]
    
    def getEventTypes(self):
        return [ 
            { "types": [Event.TYPE_DEVICE], "actions": [Event.ACTION_CREATE, Event.ACTION_MODIFY], "details": ["ip"] },
            { "types": [Event.TYPE_DEVICE_STAT, Event.TYPE_CONNECTION_STAT], "actions": [Event.ACTION_CREATE, Event.ACTION_MODIFY], "details": ["online_state","wan_type","wan_state"] } 
        ]

    def processEvents(self, events):
        for event in events:
            if event.getAction() != Event.ACTION_CREATE and event.getAction() != Event.ACTION_MODIFY:
                continue

            if event.getType() == Event.TYPE_DEVICE:
                if event.getObject().getMAC() in self.skipped_macs:
                    device = event.getObject()
                    stats = []
                    stat = self.cache.getUnlockedDeviceStat(device.getMAC())
                    if stat is not None:
                        stats.append(stat)
                    if device.getConnection() is not None:
                        stat = self.cache.getUnlockedConnectionStat(device.getConnection().getTargetMAC(), device.getConnection().getTargetInterface())
                        if stat is not None:
                            stats.append(stat)
                        
                    for stat in stats:
                        self._publishValues(device, stat)
            else:
                stat = event.getObject()
                device = stat.getUnlockedDevice()
                    
                if device is None:
                    continue

                self._publishValues(device, stat, event.getDetails())               
