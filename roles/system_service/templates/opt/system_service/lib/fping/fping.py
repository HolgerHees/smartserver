#import netflow # https://github.com/bitkeks/python-netflow-v9-softflowd
import threading
import traceback
import json
import requests
import re

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
                returncode, result = command.exec2([ "/usr/sbin/fping", "-q", "-A", "-n", "-c1" ] + self.config.fping_test_hosts, is_running_callback=self._isRunning)

                ping_result_map = {}
                if len(result) > 0:

                    lines = result.split("\n")
                    index = 0
                    for host in self.config.fping_test_hosts:
                        ping_result = lines[index]

                        match = re.search("^([^\\s]+) \\(([^\\)]+)\\)\\s*:.*?( min\\/avg\\/max\\s*=\\s*[0-9\\.]+\\/([0-9\\.]+)\\/[0-9\\.]+)?$", ping_result)
                        if match[4] is None:
                            continue

                        ping_result_map[host] = { "dns": match[1], "ip": match[2], "time": match[4] }

                        index += 1

                messurements = []
                for host in self.config.fping_test_hosts:
                    if host not in ping_result_map:
                        continue
                    messurements.append("fping,hostname={} value={}".format(host, ping_result_map[host]["time"]))

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
