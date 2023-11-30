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

import os
from smartserver.confighelper import ConfigHelper


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

        self.dump_path = "/var/lib/system_service/info.json"
        self.version = 1
        self.valid_cache_file = True

        self.active_service = 0

        self.ip_check = "8.8.8.8"
        self.ip_check_error_count = 0

        self.default_isp_connection_active = False
        self.wan_active = False

        self.default_isp = {}
        for field, pattern in config.default_isp.items():
            self.default_isp[field] = re.compile(pattern, re.IGNORECASE)

        self._restore()

    def start(self):
        self.is_running = True
        super().start()

    def terminate(self):
        #logging.info("Shutdown fping")
        if self.is_running and self.valid_cache_file and os.path.exists(self.dump_path):
            self._dump()

        self.is_running = False
        self.event.set()

    def _isRunning(self):
        return self.is_running

    def run(self):
        logging.info("Info started")
        try:
            while self._isRunning():
                #logging.info("CHECK")
                self.default_isp_connection_active = self.checkIP(self.active_service)
                #logging.info("RESULT: {}".format(self.default_isp_connection_active))
                #logging.info("active_service: {}".format(self.active_service))

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

    def _restore(self):
        self.valid_cache_file, data = ConfigHelper.loadConfig(self.dump_path, self.version )
        if data is not None:
            self.active_service = data["active_service"]
            logging.info("Loaded config")
        else:
            self.active_service = 0
            if self.valid_cache_file:
                self._dump()

    def _dump(self):
        if self.valid_cache_file:
            ConfigHelper.saveConfig(self.dump_path, self.version, { "active_service": self.active_service } )
            logging.info("Saved config")

    def checkConnection(self):
        returncode, result = command.exec2([ "/usr/sbin/fping", "-q", "-c1", self.ip_check ], isRunningCallback=self._isRunning)
        return returncode == 0

    def checkIP(self, active_service):
        try:
            response = requests.get(self.ip_urls[active_service]["url"], timeout=10)

            if not self._isRunning():
                return False

            if response.status_code == 200:
                if len(response.content) > 0:
                    try:
                        data = json.loads(response.content)
                        active_ip = data[self.ip_urls[active_service]["field"]]

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
        except requests.exceptions.ReadTimeout as e:
            logging.warn("Timeout error during fetching ip.")
            self.ip_check_error_count = 99
        except requests.exceptions.ConnectionError as e:
            logging.warn("Connection error during fetching ip.")
            self.ip_check_error_count = 99
        except:
            logging.error("Error fetching ip")
            logging.error(traceback.format_exc())

        self.ip_check_error_count += 1
        if self.ip_check_error_count > 5:
            self.ip_check_error_count = 0
            _active_service = self.active_service
            if self.active_service + 1 < len(self.ip_urls):
                self.active_service += 1
            else:
                self.active_service = 0
            logging.info("Switching ip check provider from {} to {}".format(_active_service, self.active_service))

        return self.default_isp_connection_active

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

