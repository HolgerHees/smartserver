#import netflow # https://github.com/bitkeks/python-netflow-v9-softflowd
import threading
import traceback
import json
import requests

import logging

from datetime import datetime

from smartserver import command
from smartserver.metric import Metric


class FPing(threading.Thread):
    def __init__(self, config, handler, influxdb ):
        threading.Thread.__init__(self)

        self.is_running = False
        self.event = threading.Event()

        self.config = config
        self.influxdb = influxdb

        self.messurements = []

    def start(self):
        self.is_running = True

        self.influxdb.register(self.getMessurements)

        super().start()

    def terminate(self):
        #logging.info("Shutdown fping")

        self.is_running = False
        self.event.set()
        self.join()

    def _isRunning(self):
        return self.is_running

    def run(self):
        try:
            logging.info("FPing started")
            while self._isRunning():
                returncode, result = command.exec2([ "/usr/sbin/fping", "-q", "-c1" ] + self.config.fping_test_hosts, is_running_callback=self._isRunning)

                ping_result_map = {}
                if len(result) > 0:
                    for ping_result in result.split("\n"):
                        #8.8.8.8       : xmt/rcv/%loss = 1/1/0%, min/avg/max = 8.81/8.81/8.81

                        [host, s1]          = ping_result.split(" : ")
                        if ", min/avg/max = " not in s1:
                            continue

                        [stats, ping]       = s1.split(", ")
                        [_, ping_values]    = ping.split(" = ")
                        [_, ping_value, _]  = ping_values.split("/")

                        ping_result_map[host.strip()] = ping_value.strip()

                messurements = []
                for host in self.config.fping_test_hosts:
                    if host not in ping_result_map:
                        continue
                    messurements.append("fping,hostname={} value={}".format(host, ping_result_map[host]))

                self.messurements = messurements

                self.event.wait(60)
        except Exception as e:
            self.is_running = False
            raise e
        finally:
            logging.info("FPing stopped")

    def getMessurements(self):
        return self.messurements

    def getStateMetrics(self):
        return [ Metric.buildProcessMetric("system_service", "fping", "1" if self.is_running else "0") ]
