#import netflow # https://github.com/bitkeks/python-netflow-v9-softflowd
import threading
import traceback
import json
import requests

import logging

from datetime import datetime

from smartserver import command

class FPing(threading.Thread):
    def __init__(self, config, handler, influxdb ):
        threading.Thread.__init__(self)

        self.is_running = True
        self.event = threading.Event()

        self.config = config

        self.messurements = []

        influxdb.register(self.getMessurements)

    def terminate(self):
        self.is_running = False
        self.event.set()

    def run(self):
        try:
            while self.is_running:
                result = command.exec([ "/usr/sbin/fping", "-q", "-c1" ] + self.config.fping_test_hosts, exitstatus_check = False )
                ping_results = result.stdout.decode("utf-8").strip().split("\n")

                ping_result_map = {}
                for ping_result in ping_results:
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
                self.event.clear()
        except Exception:
            logging.error(traceback.format_exc())
            self.is_running = False

    def getMessurements(self):
        return self.messurements

    def getStateMetrics(self):
        return ["system_service_process{{type=\"fping\",}} {}".format("1" if self.is_running else "0")]

