import threading
import traceback
import logging
import urllib.parse
import urllib.request
import time
import json
import re
import ipaddress
import math
from datetime import datetime

from lib.trafficwatcher.helper.helper import TrafficGroup, Helper as TrafficHelper

class Helper():
    @staticmethod
    def getServiceKey(ip, port):
        return "{}:{}".format(ip.compressed, port)

class Connection:
    def __init__(self, timestamp, target_ip, target_port, source_ip, is_suspicious, config, ipcache):
        self.start_timestamp = self.end_timestamp = timestamp

        self.dest = ipaddress.ip_address(target_ip)
        self.dest_port = target_port
        self.src = ipaddress.ip_address(source_ip)
        self.is_suspicious = is_suspicious

        self.ipcache = ipcache

        self._location = self.ipcache.getLocation(self.src, True)

        self._src_hostname = self.ipcache.getHostname(self.src, True)
        self._dest_hostname = self.ipcache.getHostname(self.dest, True)

        self.src_is_external = self.ipcache.isExternal(self.src)
        self.skipped = not self.src_is_external

        self.service = TrafficHelper.getIncommingService(self.dest, self.dest_port, config.netflow_incoming_traffic)
        if self.service is None:
            self.service = "http"

        self.protocol_name = "tcp"
        self.ip_type = "v4"
        #self.size = 0

        self.connection_type = "apache"

    def applyDebugFields(self, data):
        pass

    @staticmethod
    def mergeData(data, flow):
        if TrafficGroup.PRIORITY[data["state_tags"]["group"]] < TrafficGroup.PRIORITY[flow["state_tags"]["log_group"]]:
            data["state_tags"]["group"] = flow["state_tags"]["log_group"]

        if TrafficGroup.PRIORITY[data["state_tags"]["log_group"]] < TrafficGroup.PRIORITY[flow["state_tags"]["log_group"]]:
            data["state_tags"]["log_group"] = flow["state_tags"]["log_group"]

        if flow["state_tags"]["log_type"] != "-":
            data["state_tags"]["log_type"] = flow["state_tags"]["log_type"]

        if "log_count" in flow["values"]:
            if "log_count" in data["values"]:
                data["values"]["log_count"] += flow["values"]["log_count"]
            else:
                data["values"]["log_count"] = flow["values"]["log_count"]

    def applyData(self, data, traffic_group):
        data["state_tags"]["group"] = traffic_group
        data["state_tags"]["log_group"] = traffic_group
        data["state_tags"]["log_type"] = "apache"
        data["values"]["log_count"] = 1

    def getTrafficGroup(self, blocklist_name):
        if blocklist_name:
            return TrafficGroup.SCANNING if self.is_suspicious else TrafficGroup.OBSERVED
        return TrafficGroup.NORMAL

    def isFilteredTrafficGroup(self, traffic_group):
        return traffic_group == TrafficGroup.NORMAL

    @property
    def src_hostname(self):
        return self._src_hostname if self._src_hostname is not None else self.ipcache.getHostname(self.src, False)

    @property
    def dest_hostname(self):
        return self._dest_hostname if self._dest_hostname is not None else self.ipcache.getHostname(self.dest, False)

    @property
    def location(self):
        return self._location if self._location is not None else self.ipcache.getLocation(self.src, False)

class LogCollector(threading.Thread):
    def __init__(self, config, watcher, ipcache):
        threading.Thread.__init__(self)

        self.is_running = False

        self.event = threading.Event()

        self.config = config
        self.watcher = watcher
        self.ipcache = ipcache

        self.last_fetch = None
        self.processed_lines = {}

        server_ports = []
        for service in self.config.netflow_incoming_traffic:
            if self.config.netflow_incoming_traffic[service]["logs"] != "apache":
                continue
            ip, port = service.split(":")
            if ip != self.config.server_ip:
                continue
            server_ports.append(port)

        self.query = "{{group=\"apache\"}} |~ \" vhost={}:({}) \" != \" status=200 \"".format(self.config.server_domain, "|".join(server_ports)) if len(server_ports) > 0 else None
        self.limit = 10000

    def start(self):
        if self.query is not None:
            self.is_running = True
            super().start()
        else:
            logging.info("IP log collector disabled. There are is no 'netflow_incoming_traffic' with a 'log' attribute configured.")

    def terminate(self):
        if self.query is not None:
            self.is_running = False
            self.event.set()

    def run(self):
        logging.info("IP log collector started")
        try:
            while self.is_running:
                # merge http requests
                self._processHttpRequests()
                self.event.wait(60)

            logging.info("IP log collector stopped")
        except Exception:
            logging.error(traceback.format_exc())
            self.is_running = False

    def _processHttpRequests(self):
        try:
            now = time.time()
            if self.last_fetch == None:
                start = self.watcher.getLastTrafficEventTime("apache")
                #logging.info(start)
                if start == 0:
                    start = now - self.config.traffic_blocker_unblock_timeout
                else:
                    start += 0.001
            else:
                start = self.last_fetch - 60 # grep last minute again, to collect also late occuring log lines

            #logging.info("FETCH {}".format(datetime.fromtimestamp(start)))
            url = "{}/loki/api/v1/query_range?start={}&limit={}&direction=forward&query={}".format(self.config.loki_rest, start, self.limit, urllib.parse.quote(self.query))
            #logging.info(self.query)
            #logging.info(url)
            contents = urllib.request.urlopen(url).read()
            result = json.loads(contents)
            external_state = {}
            last_processed_timestamp = 0
            if "status" in result and result["status"] == "success":
                new_events = 0
                all_events = 0
                processed_lines = {}
                for result in result["data"]["result"]:
                    for row in result["values"]:
                        all_events += 1

                        key = "{}-{}".format(row[0], row[1])
                        if key in self.processed_lines:
                            #logging.info("SKIP log line {}".format(row[1]))
                            continue

                        timestamp = int(row[0]) / 1000000000
                        processed_lines[key] = timestamp

                        #logging.info("{} {}".format(datetime.fromtimestamp(int(row[0]) / 1000000000), row[1]))
                        # message ${record["host"] + " - " + record["user"] + " - " + record["domain"] + " - " + record["request"] + " - " + record["code"] + " - " + record["message"]}
                        #                            IP         USER     DOMAIN   REQUEST
                        match = re.match("^remoteIP=([^\s]+).*?vhost=(.*?) request=(.*?) status=",row[1])
                        if not match:
                            logging.error("Invalid regex for message: '{}'".format(row[1]))
                            continue

                        ip = match[1]

                        #if ip in self.approved_ips:
                        #    continue

                        #if ip not in external_state:
                        #    external_state[ip] = self.ipcache.isExternal(ipaddress.ip_address(ip))
                        #if not external_state[ip]:
                        #    continue

                        vhost = match[2].strip('"')
                        domain, port = vhost.split(":")
                        request = match[3].strip('"')

                        match = re.match("^([A-Z]+) (.+) HTTP",request)
                        if not match:
                            is_suspicious = True
                            #logging.info("===============> INVALID TIME: {}/{}, IP: {}, PORT: {}, REQUEST: {}".format(datetime.fromtimestamp(timestamp), timestamp, ip, port, request))
                        else:
                            method = match[1]
                            url = match[2]
                            #is_suspicious = method != "GET" or not re.match("^/(|.well-known|state|robots.txt|favicon.ico)$", url)
                            is_suspicious = method != "GET" or not re.match("^/(|favicon.ico)$", url)
                            #logging.info("===============> VALID TIME: {}/{}, IP: {}, PORT: {}, METHOD: {}, URL: {}".format(datetime.fromtimestamp(timestamp), timestamp, ip, port, method, url))

                        #logging.info("===============> {} {}".format(ip, request))

                        self.watcher.addConnection(Connection(timestamp, self.config.server_ip, port, ip, is_suspicious, self.config, self.ipcache))
                        new_events += 1

                logging.info("Processing of {}/{} log lines newer then {} ({})".format(new_events, all_events, datetime.fromtimestamp(start), start))
                if all_events == self.limit:
                    logging.error("Loki query limit of {} reached".format(self.limit))
            else:
                logging.info("Loki request '{}' not successful".format(url))

            # cleanup processed logs
            for key in list(self.processed_lines.keys()):
                if now - self.processed_lines[key] > 120:
                    del self.processed_lines[key]

            self.processed_lines |= processed_lines
            self.last_fetch = now

        except urllib.error.HTTPError as e:
            logging.info(e)
            #logging.info(traceback.format_exc())
            logging.info("Loki not reachable")

    def _restore(self):
        self.valid_list_file, data = ConfigHelper.loadConfig(self.dump_config_path, self.config_version )
        if data is not None:
            self.config_map = data["map"]
            logging.info("Loaded config")
        else:
            self.config_map = {"observed_ips": {}}
            self._dump()

    def _dump(self):
        if self.valid_config_file:
            with self.config_lock:
                ConfigHelper.saveConfig(self.dump_config_path, self.config_version, { "map": self.config_map } )
                logging.info("Saved config")

    def _cleanup(self):
        now = time.time()
        cleaned = 0
        with self.config_lock:
            for ip in list(self.config_map["observed_ips"].keys()):
                data = self.config_map["observed_ips"][ip]
                if data["state"] != "unblocked" or now < data["updated"] + self.config.traffic_blocker_clean_known_ips_timeout:
                    continue
                del self.config_map["observed_ips"][ip]
                cleaned = cleaned + 1
        if cleaned > 0:
            logging.info("Cleaned {} ip(s)".format(cleaned))

    def getApprovedIPs(self):
        return list(self.approved_ips)

    def getBlockedIPs(self):
        return list(self.blocked_ips)

    def getMessurements(self):
        messurements = []
        if self.config_map is not None:
            with self.config_lock:
                for ip, data in self.config_map["observed_ips"].items():
                    if data["state"] != "blocked":
                        continue
                    messurements.append("trafficblocker,extern_ip={},blocking_state={},blocking_reason={},blocking_type={},blocking_count={} value=\"{}\"".format(ip, data["state"], data["reason"], data["type"], data["count"], data["last"]))
        return messurements

    def getStateMetrics(self):
        return [ "system_service_process{{type=\"trafficwatcher.logcollector\"}} {}".format("1" if self.is_running else "0") ]
