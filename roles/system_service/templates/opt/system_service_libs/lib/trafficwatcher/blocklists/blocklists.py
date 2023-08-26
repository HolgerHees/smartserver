import threading
import logging
import traceback
import time
import socket
import ipaddress
import re

import requests
import json

import schedule
import os
from datetime import datetime, timedelta

from smartserver.confighelper import ConfigHelper

class Blocklists(threading.Thread):
    def __init__(self, config, influxdb):
        threading.Thread.__init__(self)

        self.is_running = False

        self.event = threading.Event()

        self.configs = {
            "blocklist": { "do": schedule.every().hour.at("00:00"), "version": 1, "url": "https://lists.blocklist.de/lists/all.txt", "process": self._processFail2Ban },
            "ipsum": { "do": schedule.every().day.at("04:00"), "version": 1, "url": "https://raw.githubusercontent.com/stamparm/ipsum/master/ipsum.txt", "process": self._processIPSum } # list is normally updated at 3am
        }

        self.dump_path_template = "/var/lib/system_service/blocklists_{}.json"
        self.valid_dump_file = {}

        self.map_modified = {}
        self.map_data = {}

        self.max_list_age = 60 * 60 * 24 * 7

        self.check_map = {}

        self._restore()

    def start(self):
        self.is_running = True

        for name, config in self.configs.items():
            config["do"].do(lambda name=name: self._fetch(name))

        schedule.every().day.at("05:00").do(self._dumpAll)
        #influxdb.register(self.getMessurements)

        super().start()

    def terminate(self):
        if self.is_running:
            for name, config in self.configs.items():
                if os.path.exists(self.dump_path_template.format(name)):
                    self._dump(name)

        self.is_running = False
        self.event.set()

    def run(self):
        logging.info("IP blocklist handler started")
        try:
            while self.is_running:
                self.event.wait(60)

            logging.info("IP blocklist handler  stopped")
        except Exception:
            logging.error(traceback.format_exc())
            self.is_running = False

    def _restore(self):
        for name, config in self.configs.items():
            self.valid_dump_file[name], data = ConfigHelper.loadConfig(self.dump_path_template.format(name), config["version"])
            if data is not None:
                self.map_data[name] = data["map"]
                self.map_modified[name] = data["map_modified"]
                logging.info("Loaded {} blocklist {} ip's".format(len(self.map_data[name]), name))
            else:
                self.map_data[name] = {}
                self._fetch(name)
                self._dump(name)
        self._build()

    def _dumpAll(self):
        for name, config in self.configs.items():
            if name not in self.map_data:
                continue
            self._dump(name)

    def _dump(self, name):
        if self.valid_dump_file[name]:
            ConfigHelper.saveConfig(self.dump_path_template.format(name), self.configs[name]["version"], { "map_modified": self.map_modified[name], "map": self.map_data[name] } )
            logging.info("Saved {} blocklist {} ip's".format(name, len(self.map_data[name])))

    def _fetch(self, name):
        try:
            url = self.configs[name]["url"]
            response = requests.get(url)
            if response.status_code == 200:
                if len(response.content) > 0:
                    content = response.content.decode("utf-8")
                    lines = []
                    for line in content.splitlines():
                        if len(line.strip()) == 0:
                            continue
                        lines.append(line)

                    map_data, map_modified, created, deleted = self.configs[name]["process"](name, lines)
                    if (created > 0 or deleted > 0) and map_modified is not None:
                        self.map_data[name] = map_data
                        self.map_modified[name] = map_modified

                        logging.info("Process {} - created: {}, deleted: {}".format(name, created, deleted))

                        self._build()
                    elif len(map_data) == 0:
                        logging.error("Error parsing {} list. Got empty map data".format(name))
                else:
                    logging.error("Error fetching {} list. Got empty response".format(name))
            else:
                logging.error("Error fetching {} list. Got code: '{}' and repsonse: '{}'".format(name, response.status_code, response.content))

        except:
            logging.error("Error fetching ipsum list")
            logging.error(traceback.format_exc())
            return

    def _processIPSum(self, name, lines):
        created = deleted = 0

        map_modified = None
        map_data = {}
        map_with_errors = False
        for line in lines:
            if line.startswith("#"):
                if line.startswith("# Last update: "):
                    datetime_str = line[15:]
                    map_modified = datetime.timestamp(datetime.strptime(datetime_str, '%a, %d %b %Y %H:%M:%S %z' ))
                continue

            columns = re.split("\s+", line)
            if len(columns) != 2:
                logging.warning("Skip invalid list entry. Invalid format. '{}'".format(line))
                map_with_errors = True
                #return [None, None]
                continue

            amount = int(columns[1])
            if amount < 2:
                continue

            if columns[0] not in self.map_data[name]:
                created += 1
            map_data[columns[0]] = amount

        if map_with_errors:
            if len(map_data) <= len(self.map_data[name]):
                logging.warning("Skip invalid map. Map has invalid enties and is less then before")
                return [None, None, 0, 0, 0]
            else:
                logging.warning("Keep invalid map. Map has more enties then before")

        deleted = len(self.map_data[name]) - (len(map_data) - created)

        return [map_data,map_modified,created,deleted]

    def _processFail2Ban(self, name, lines):
        if len(lines) > 0 and "ERROR" in lines[0]:
            return False

        created = deleted = 0

        map_modified = None
        map_data = {}
        for line in lines:
            if line not in self.map_data[name]:
                created += 1
            map_data[line] = 1
        map_modified = time.time()

        deleted = len(self.map_data[name]) - (len(map_data) - created)

        return [map_data,map_modified,created,deleted]

    def _build(self):
        start = time.time()

        check_map = {}
        for name, ips in self.map_data.items():
            for ip in ips.keys():
                if ip in check_map:
                    continue
                check_map[ip] = name
        self.check_map = check_map

        end = time.time()
        logging.info("Rebuild malware check map in {} seconds".format(round(end-start,2)))

    def check(self, ip):
        return self.check_map[ip] if ip in self.check_map else None

    def getStateMetrics(self):
        metrics = [
            "system_service_process{{type=\"trafficwatcher.malware\",}} {}".format("1" if self.is_running else "0")
        ]

        for name, config in self.configs.items():
            metrics.append("system_service_blocklists{{listname=\"{}\",type=\"state\"}} {}".format(name, 1 if ( name in self.map_modified and self.map_modified[name] > time.time() - self.max_list_age ) else 0))
            metrics.append("system_service_blocklists{{listname=\"{}\",type=\"last_modified\"}} {}".format(name, self.map_modified[name] if name in self.map_modified else 0))
            metrics.append("system_service_blocklists{{listname=\"{}\",type=\"entries\"}} {}".format(name, len(self.map_data[name].keys())))
            metrics.append("system_service_state{{type=\"trafficwatcher.malware\",details=\"{}_file\"}} {}".format(name, "1" if self.valid_dump_file[name] else "0"))

        return metrics
