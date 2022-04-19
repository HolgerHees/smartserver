import threading
from datetime import datetime

import logging

from lib.handler import _handler
from lib.dto.event import Event
import paho.mqtt.client as mqtt


class MQTTHandler(): 
    def __init__(self):
        self.mqtt_client = None
              
    def start(self):
        logging.info("Connection to mqtt ...")
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = lambda client, userdata, flags, rc: self.on_connect(client, userdata, flags, rc)
        self.mqtt_client.on_disconnect = lambda client, userdata, rc: self.on_disconnect(client, userdata, rc)
        self.mqtt_client.on_message = lambda client, userdata, msg: self.on_message(client, userdata, msg) 
        self.mqtt_client.connect("mosquitto", 1883, 60)
        
        self.mqtt_client.loop_start()

    def on_connect(self,client,userdata,flags,rc):
        logging.info("Connected to mqtt with result code:"+str(rc))
        
    def on_disconnect(self,client, userdata, rc):
        logging.info("Disconnect from mqtt with result code:"+str(rc))

    def on_message(self,client,userdata,msg):
        logging.info("Topic " + msg.topic + ", message:" + str(msg.payload))
        
    def publish(self, name, payload):
        self.mqtt_client.publish('system_info/{}'.format(name), payload=payload, qos=0, retain=False)
            
    def terminate(self):
        if self.mqtt_client is not None:
            logging.info("Close connection to mqtt")
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
            

class MQTTPublisher(_handler.Handler): 
    def __init__(self, config, cache ):
        super().__init__()
      
        self.is_running = True
      
        self.config = config
        self.cache = cache
        
        self.skipped_macs = {}
        self.allowed_details = {}
        
        self.mqtt_handler = MQTTHandler()
        
        self.published_values = {}
        
        self.condition = threading.Condition()
        self.thread = threading.Thread(target=self._checkPublishedValues, args=())

    def start(self):
        self.mqtt_handler.start() 
        self.thread.start()
        
    def terminate(self):
        with self.condition:
            self.is_running = False
            self.condition.notifyAll()

        self.mqtt_handler.terminate() 
        
    def _checkPublishedValues(self):
        while self.is_running:
            now = datetime.now()
            timeout = self.config.publisher_republish_interval
            
            for mac in list(self.published_values.keys()):
                if self.cache.getUnlockedDevice(mac) is None:
                    del self.published_values[mac]
                    continue
                
                for key in self.published_values[mac]:
                    [last_publish, value] = self.published_values[mac][key]
                    
                    _diff = (now-last_publish).total_seconds()
                    if _diff >= self.config.publisher_republish_interval:
                        #logging.info("republish")
                        self._publishValue(mac, key, value)
                    else:
                        _timeout = self.config.publisher_republish_interval - _diff
                        if _timeout < timeout:
                            timeout = _timeout

            with self.condition:
                #logging.info("sleep {}".format(timeout))
                self.condition.wait(timeout)
    
    def _publishValues(self, device, stat, changed_details = None):
        mac = device.getMAC()
        
        if device.getIP() is None:
            self.skipped_macs[mac] = True
            return False

        ip = device.getIP()
        if ip not in self.allowed_details:
            self.allowed_details[ip] = [] #["signal"]
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

        logging.info("PUBLISH {} of {}".format(_details, device))

        for detail in _details:
            #if detail == "signal":
            #    self.mqtt_handler.publish("network/{}/{}".format(device.getIP(),"signal"), stat.getDetail("signal") )
            if detail == "online_state":
                key = "network/{}/{}".format(device.getIP(),"online")
                value = "ON" if stat.isOnline() else "OFF"
                self._publishValue(mac, key, value)
                
        with self.condition:
            self.condition.notifyAll()

        return True
    
    def _publishValue(self, mac, key, value):
        if mac not in self.published_values:
            self.published_values[mac] = {}
            
        self.mqtt_handler.publish(key, value )
        self.published_values[mac][key] = [datetime.now(), value]
    
    def getEventTypes(self):
        return [ { "types": [Event.TYPE_DEVICE, Event.TYPE_STAT], "actions": [Event.ACTION_CREATE, Event.ACTION_MODIFY], "details": None } ]

    def processEvents(self, events):
        for event in events:
            if event.getAction() != Event.ACTION_CREATE and event.getAction() != Event.ACTION_MODIFY:
                continue

            if event.getType() == Event.TYPE_DEVICE:
                if event.getObject().getMAC() in self.skipped_macs:
                    device = event.getObject()
                    stat = self.cache.getUnlockedStat(device.getMAC())
                    if stat is not None and self._publishValues(device, stat):
                        del self.skipped_macs[device.getMAC()]
            elif event.getType() == Event.TYPE_STAT:
                stat = event.getObject()
                if stat.getInterface() is not None:
                    continue

                device = self.cache.getUnlockedDevice(stat.getMAC())
                self._publishValues(device, stat, event.getDetails())               
        return []
