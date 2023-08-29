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

from lib.ipcache import IPCache


class Info(threading.Thread):
    def __init__(self, config, ipcache ):
        threading.Thread.__init__(self)

        self.is_running = False
        self.event = threading.Event()

        self.config = config

        self.ipcache = ipcache

        self.ip_urls = [
            {"url": "https://natip.tuxnet24.de/index.php?mode=json", "field": "ip-address"},
            {"url": "https://api.ipify.org/?format=json", "field": "ip"}
        ]
        self.active_url = 0

        self.ip_check = "8.8.8.8"
        self.ip_check_error_count = 0

        self.default_isp_connection_active = False
        self.wan_active = False

        self.default_isp = {}
        for field, pattern in config.default_isp.items():
            self.default_isp[field] = re.compile(pattern, re.IGNORECASE)

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

                if not self._isRunning():
                    break

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
            response = requests.get(self.ip_urls[self.active_url]["url"])

            if not self._isRunning():
                return False

            if response.status_code == 200:
                if len(response.content) > 0:
                    try:
                        data = json.loads(response.content)
                        active_ip = data[self.ip_urls[self.active_url]["field"]]

                        if "org" in self.default_isp:
                            result = self.ipcache.getLocation(ipaddress.ip_address(active_ip), False)

                            if not self._isRunning():
                                return False

                            if result["type"] == IPCache.TYPE_LOCATION:
                                location_org = result["org"] if result["org"] else ( result["isp"] if result["isp"] else "" )
                                if self.default_isp["org"].match(location_org):
                                    self.ip_check_error_count = 0
                                    return True

                        if "hostname" in self.default_isp:
                            hostname = self.ipcache.getHostname(ipaddress.ip_address(active_ip), False)
                            if self.default_isp["hostname"].match(hostname):
                                self.ip_check_error_count = 0
                                return True

                        if "ip" in self.default_isp:
                            if self.default_isp["ip"].match(active_ip):
                                self.ip_check_error_count = 0
                                return True

                        self.ip_check_error_count = 0
                        return False
                    except:
                        logging.error("Error parsing ip")
                        logging.error(":{}:".format(response.content))
                        logging.error(traceback.format_exc())
                else:
                    logging.error("Error fetching ip. Got empty response")
            else:
                logging.error("Error fetching ip. Got code: '{}' and repsonse: '{}'".format(response.status_code, response.content))
        except requests.exceptions.ConnectionError as e:
            logging.warn("Connection error during fetching ip.")
        except:
            logging.error("Error fetching ip")
            logging.error(traceback.format_exc())

        self.ip_check_error_count += 1
        if self.ip_check_error_count <= 5:
            return self.default_isp_connection_active
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

