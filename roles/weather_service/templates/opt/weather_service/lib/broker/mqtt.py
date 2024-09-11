import paho.mqtt.client as mqtt

import traceback

import time
import threading
import logging
import re


class MQTT(threading.Thread):
    '''Handler client'''
    def __init__(self, config):
        threading.Thread.__init__(self)

        self.is_running = False
        self.config = config

        self.event = threading.Event()

        self.lock = threading.Lock()

        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = lambda client, userdata, flags, rc: self.on_connect(client, userdata, flags, rc)
        self.mqtt_client.on_disconnect = lambda client, userdata, rc: self.on_disconnect(client, userdata, rc)
        self.mqtt_client.on_message = lambda client, userdata, msg: self.on_message(client, userdata, msg)

        self.subscriber = {}

        self.state = -1

    def start(self):
        self.is_running = True
        super().start()

    def run(self):
        # must run as first, otherwise subscribe and publish from other services will fail
        while self.is_running:
            try:
                logging.info("Connection to mqtt ...")
                self.mqtt_client.connect(self.config.mosquitto_host, 1883, 60)
                self.mqtt_client.loop_start()
                break
            except Exception as e:
                logging.info("MQTT {}. Retry in 5 seconds".format(str(e)))
                time.sleep(5)

        while self.is_running:
            self.event.wait(60)
            self.event.clear()

    def on_connect(self,client,userdata,flags,rc):
        logging.info("Connected to mqtt with result code:"+str(rc))
        with self.lock:
            for topic in self.subscriber:
                logging.info("Activate subscription for '{}'".format(topic))
                self.mqtt_client.subscribe(topic)
        self.state = 1

    def on_disconnect(self,client, userdata, rc):
        logging.info("Disconnect from mqtt with result code:"+str(rc))
        self.state = 0

    def on_message(self,client,userdata,msg):
        for topic in self.subscriber:
            pattern = topic.replace("+" , "[^/]*").replace("#", ".*")
            #logging.info("{} {} {}".format(pattern, msg.topic, re.match(pattern, msg.topic) ))
            if re.match(pattern, msg.topic):
                self.subscriber[topic](client,userdata,msg)

    def subscribe(self, topic, callback):
        with self.lock:
            self.subscriber[topic] = callback
            if self.mqtt_client.is_connected():
                logging.info("Subscribe for '{}'".format(topic))
                self.mqtt_client.subscribe(topic)
            else:
                logging.info("Save subscribtion for '{}'".format(topic))

    def publish(self, topic, payload=None, qos=0, retain=False):
        self.mqtt_client.publish(topic, payload,qos,retain)

    def isConnected(self):
        return self.mqtt_client.is_connected()

    def getStateMetrics(self):
        return ["weather_service_state{{type=\"mqtt\"}} {}".format(self.state)]

    def terminate(self):
        self.is_running = False
        self.event.set()

        if self.mqtt_client != None:
            logging.info("Close connection to mqtt")
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
