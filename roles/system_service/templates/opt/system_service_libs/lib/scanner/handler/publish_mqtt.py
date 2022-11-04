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
        
        self._setServiceMetricState("mqtt", -1)

    def start(self):
        super().start()

        self._setServiceMetricState("mqtt", 1)

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
                        if _device is None:
                            Helper.logInfo("CLEAN values of {}".format(mac))
                            del self.published_values[mac]
                            continue
                        
                        _to_publish = {}
                        for [detail, topic, value, last_publish] in self.published_values[mac].values():
                            
                            _diff = (now-last_publish).total_seconds()
                            if _diff >= self.config.mqtt_republish_interval:
                                _to_publish[detail] = [detail, topic, value]
                            else:
                                _timeout = self.config.mqtt_republish_interval - _diff
                                if _timeout < timeout:
                                    timeout = _timeout
                                    
                        if len(_to_publish) > 0:
                            Helper.logInfo("REPUBLISH {} of {}".format(list(_to_publish.keys()), _device))
                            for [detail, topic, value] in _to_publish.values():
                                self._publishValue(mac, detail, topic, value, now)

                    self._setServiceMetricState("mqtt", 1)

                except Exception as e:
                    self._handleUnexpectedException(e)
                    self._setServiceMetricState("mqtt", -1)

            suspend_timeout = self._getSuspendTimeout()
            if suspend_timeout > 0:
                timeout = suspend_timeout

            self._wait(timeout)

    def _publishValues(self, device, stat, changed_details = None):
        mac = device.getMAC()
        
        if device.getIP() is None:
            self.skipped_macs[mac] = True
            return False

        ip = device.getIP()
        if ip not in self.allowed_details:
            self.allowed_details[ip] = ["wan_type","wan_state"]
            if ip in self.config.user_devices:
                self.allowed_details[ip].append("online_state")
        
        _details = []
        if changed_details is None:
            _details = self.allowed_details[ip]
        else:
            for detail in changed_details:
                if detail not in self.allowed_details[ip]:
                    continue
                _details.append(detail)
                
        if len(_details) == 0:
            return False

        _to_publish = {}
        if type(stat) is DeviceStat:
            for detail in _details:
                if detail == "online_state":
                    topic = "network/{}/{}".format(device.getIP(),"online")
                    value = "ON" if stat.isOnline() else "OFF"
                    _to_publish[detail] = [detail,topic,value]
        else:
            for detail in _details:
                #if detail == "signal":
                #    self.mqtt.publish("network/{}/{}".format(device.getIP(),"signal"), stat.getDetail("signal") )
                for data in stat.getDataList():
                    if detail in ["wan_type","wan_state"] and data.getDetail(detail) is not None:
                        topic = "network/{}/{}".format(device.getIP(),detail)
                        _to_publish[detail] = [detail,topic,data.getDetail(detail)]
                
        if len(_to_publish.values()) == 0:
            return False

        Helper.logInfo("PUBLISH {} of {}".format(list(_to_publish.keys()), device))

        now = datetime.now()
        for [detail, topic, value] in _to_publish.values():
            self._publishValue(mac, detail, topic, value, now)
                
        self._wakeup()

        return True
    
    def _publishValue(self, mac, detail, topic, value, now):
        if mac not in self.published_values:
            self.published_values[mac] = {}
            
        self.mqtt.publish(topic, value )
        self.published_values[mac][topic] = [detail, topic, value, now]
    
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
                        
                    all_stats_published = True
                    for stat in stats:
                        if not self._publishValues(device, stat):
                            all_stats_published = False
                    if all_stats_published and device.getMAC() in self.skipped_macs:
                        del self.skipped_macs[device.getMAC()]

            else:
                stat = event.getObject()
                device = stat.getUnlockedDevice()
                    
                if device is None:
                    continue

                self._publishValues(device, stat, event.getDetails())               
