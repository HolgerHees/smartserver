#import netflow # https://github.com/bitkeks/python-netflow-v9-softflowd
import threading
import traceback
import json
import requests
import ipaddress
import re

import logging

from datetime import datetime

from smartserver import command

class Info(threading.Thread):
    def __init__(self, config, ipcache ):
        threading.Thread.__init__(self)

        self.is_running = False
        self.event = threading.Event()

        self.config = config

        self.ipcache = ipcache

        self.ip_url = "https://natip.tuxnet24.de/index.php?mode=json"
        self.ip_check = "8.8.8.8"

        self.default_isp_connection_active = False
        self.wan_active = False

        self.default_isp_pattern = re.compile(config.default_isp_pattern, re.IGNORECASE) if config.default_isp_pattern is not None else None

    def start(self):
        self.is_running = True
        super().start()

    def terminate(self):
        #logging.info("Shutdown fping")

        self.is_running = False
        self.event.set()

    def _isRunning(self):
        return self.is_running

    def run(self):
        logging.info("Info started")
        try:
            while self._isRunning():
                self.default_isp_connection_active = self.checkIP()
                self.wan_active = self.checkConnection()

                if self.default_isp_connection_active:
                    self.wan_active = True
                else:
                    self.wan_active = self.checkConnection()

                self.event.wait(60)

            logging.info("Info stopped")
        except Exception:
            logging.error(traceback.format_exc())
            self.is_running = False

    def checkConnection(self):
        returncode, result = command.exec2([ "/usr/sbin/fping", "-q", "-c1", self.ip_check ], isRunningCallback=self._isRunning)
        return returncode == 0

    def checkIP(self):
        try:
            response = requests.get(self.ip_url)
        except:
            logging.error("Error fetching ip")
            logging.error(traceback.format_exc())
            return

        if response.status_code == 200:
            if len(response.content) > 0:
                try:
                    data = json.loads(response.content)
                    active_ip = data["ip-address"]

                    result = self.ipcache.getLocation(ipaddress.ip_address(active_ip), False)
                    if self.default_isp_pattern.match(result["org"]):
                        return True
                    if self.default_isp_pattern.match(result["isp"]):
                        return True
                except:
                    logging.error("Error parsing ip")
                    logging.error(":{}:".format(response.content))
                    logging.error(traceback.format_exc())
            else:
                logging.error("Error fetching ip. Got empty response")
        else:
            logging.error("Error fetching ip. Got code: '{}' and repsonse: '{}'".format(response.status_code, response.content))

        return False

    def isDefaultConnection(self):
        return self.default_isp_connection_active

    def isConnectionOnline(self):
        return self.wan_active

    def getMessurements(self):
        return []

    def getStateMetrics(self):
        return [
            "system_service_info{{type=\"wan_active\"}} {}".format("1" if self.wan_active else "0"),
            "system_service_info{{type=\"default_isp\"}} {}".format("1" if self.default_isp_connection_active else "0"),
            "system_service_process{{type=\"info\",}} {}".format("1" if self.is_running else "0")
        ]

