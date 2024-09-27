import paho.mqtt.client as mqtt

import traceback

import time
import threading
import logging
import re

from smartserver.metric import Metric


class Message():
    def __init__(self, topic, payload):
        self.topic = topic
        self.payload = payload

class Dummy():
    '''Handler client'''
    def __init__(self, config, lazyStart):
        self.is_running = True
        self.config = config
        self.lazyStart = lazyStart

        self.state = -1

        self.subscriber = {}

    def start(self):
        logging.info("Start dummy broker ...")

        self.lazyStart()

    def publish(self, topic, payload=None, qos=0, retain=False):
        msg = Message(topic, payload)
        for topic in self.subscriber:
            pattern = topic.replace("+" , "[^/]*").replace("#", ".*")
            #logging.info("{} {} {}".format(pattern, msg.topic, re.match(pattern, msg.topic) ))
            if re.match(pattern, msg.topic):
                self.subscriber[topic]("local", None, msg)

    def subscribe(self, topic, callback):
        self.subscriber[topic] = callback

    def getStateMetrics(self):
        return [
            Metric.buildStateMetric("weather_service", "mqtt", "connection", self.state )
        ]

    def terminate(self):
        logging.info("Stop dummy broker ...")
