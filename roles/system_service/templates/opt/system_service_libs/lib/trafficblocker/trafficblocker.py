import threading
import traceback
import logging
import time
import schedule
import os
import math
from datetime import datetime, timedelta
import urllib.parse
import urllib.request
import json
import re
import ipaddress
#import cProfile as profile
#import pstats
#import io

from smartserver.confighelper import ConfigHelper

from lib.trafficblocker.helper import Helper
from lib.netflow.processor import TrafficGroup


class TrafficBlocker(threading.Thread):
    def __init__(self, config, handler, influxdb, ipcache, netflow, malware):
        threading.Thread.__init__(self)

        self.config = config
        self.netflow = netflow
        self.malware = malware

        self.is_running = False

        self.event = threading.Event()

        self.config_lock = threading.Lock()

        self.dump_config_path = "/var/lib/system_service/trafficblocker.json"
        self.config_version = 3
        self.valid_config_file = True
        self.config_map = None

        self.blocked_ips = []
        self.approved_ips = []

        self.ipcache = ipcache
        self.influxdb = influxdb

        self._restore()

    def start(self):
        self.is_running = True

        schedule.every().day.at("01:00").do(self._dump)
        schedule.every().hour.at("00:00").do(self._cleanup)
        self.influxdb.register(self.getMessurements)

        super().start()

    def terminate(self):
        if self.is_running and os.path.exists(self.dump_config_path):
            self._dump()
        self.is_running = False
        self.event.set()

    def run(self):
        logging.info("IP traffic blocker started")
        try:
            self.blocked_ips = []

            HIERARCHY = {
                "netflow_{}".format(TrafficGroup.SCANNING): ["netflow_{}".format(TrafficGroup.INTRUDED)],
                "netflow_{}".format(TrafficGroup.OBSERVED): ["netflow_{}".format(TrafficGroup.SCANNING), "netflow_{}".format(TrafficGroup.INTRUDED)],
            }

            while self.is_running:
                #runtime_start = time.time()
                #prof = profile.Profile()
                #prof.enable()

                now = time.time()
                blocked_ips = Helper.getBlockedIps()
                ip_traffic_state = self.netflow.getIPTrafficState()

                #checked_ips = []
                #for ip in blocked_ips:
                #    if ip in checked_ips:
                #        logging.info("unblock")
                #        Helper.unblockIp(ip)
                #        #blocked_ips.remove(ip)
                #    else:
                #        checked_ips.append(ip)
                #blocked_ips = checked_ips

                #logging.info(blocked_ips)

                #for ip, data in self.config_map["observed_ips"].items():
                #    if data["type"] == "apache":
                #        del data["group"]
                #        data["reason"] = "logs"
                #        data["type"] = "apache"
                #        data["details"] = ""
                #    elif data["reason"] == "netflow":
                #        #data["type"] = "apache"
                #        data["details"] = data["group"]
                #        del data["group"]

                # post processing data
                for ip, group_data in ip_traffic_state.items():
                    if len(group_data) == 1:
                        continue
                    for group in group_data.keys():
                        if group not in HIERARCHY:
                            continue
                        for sub_group in HIERARCHY[group]:
                            if sub_group in group_data:
                                group_data[group]["count"] += group_data[sub_group]["count"]

                # merge http requests
                http_requests = self._getHttpRequests()
                for ip, data in http_requests.items():
                    if ip not in ip_traffic_state:
                        ip_traffic_state[ip] = {}
                    ip_traffic_state[ip]["apache_{}".format(data["details"])] = { "count": data["count"], "reason": "apache", "type": data["type"], "details": data["details"], "last": data["last"]}

                with self.config_lock:
                    for ip, group_data in ip_traffic_state.items():
                        #logging.info("===> {}".format(ip))

                        if ip in self.config_map["observed_ips"]:
                            data = self.config_map["observed_ips"][ip]
                            if data["state"] == "approved": # unblock validated ip
                                continue

                            for group_key, group_data in group_data.items():
                                if group_data["last"] > data["last"]:
                                    data["last"] = group_data["last"]

                            if data["state"] == "blocked": # restore state
                                if ip not in blocked_ips:
                                    Helper.blockIp(ip)
                                    blocked_ips.append(ip)
                                    logging.info("BLOCK IP {}, state: blocked".format(ip))
                                continue

                        for group_key, group_data in group_data.items():
                            #logging.info("{} {} {} {}".format(ip, group_key, group_data["count"], datetime.fromtimestamp(group_data["last"])))
                            #logging.info("{} {} {} {}".format(group_key, group_data["reason"], group_data["type"], group_data["details"]))

                            treshold = self.config.traffic_blocker_treshold[group_key]
                            if ip in self.config_map["observed_ips"]:
                                treshold = math.ceil( treshold / ( data["count"] + 1 ) ) # calculate treshhold based on number of blocked periods

                            if group_data["count"] > treshold:
                                if ip in self.config_map["observed_ips"]:
                                    data = self.config_map["observed_ips"][ip]
                                    data["updated"] = now
                                    data["state"] = "blocked"
                                    data["reason"] = group_data["reason"]
                                    data["type"] = group_data["type"]
                                    data["details"] = group_data["details"]
                                    if ip not in blocked_ips:
                                        data["count"] += 1
                                else:
                                    self.config_map["observed_ips"][ip] = {
                                        "created": now,
                                        "updated": now,
                                        "last": group_data["last"],
                                        "count": 1,
                                        "state": "blocked",
                                        "reason": group_data["reason"],
                                        "type": group_data["type"],
                                        "details": group_data["details"]
                                    }

                                if ip not in blocked_ips:
                                    Helper.blockIp(ip)
                                    blocked_ips.append(ip)
                                    logging.info("BLOCK IP {} after {} samples ({} - {} - {})".format(ip, group_data["count"], group_data["reason"], group_data["type"], group_data["details"]))

                                break

                    for ip in blocked_ips:
                        if ip in self.config_map["observed_ips"]:
                            data = self.config_map["observed_ips"][ip]
                            if data["state"] == "blocked":
                                if ip in ip_traffic_state:
                                    continue
                                factor = pow(2,data["count"] - 1)
                                time_offset = data["last"] + ( self.config.traffic_blocker_unblock_timeout * factor )
                                if now <= time_offset:
                                    continue
                                data["updated"] = now
                                data["state"] = "unblocked"
                                logging.info("UNBLOCK IP {} after {}".format(ip, timedelta(seconds=(now - data["last"]))))
                            else:
                                logging.info("UNBLOCK IP {}, state: ".format(ip, data["state"]))
                        else:
                            logging.info("UNBLOCK IP {}, state: unexpected".format(ip))

                        Helper.unblockIp(ip)
                        blocked_ips.remove(ip)

                    self.blocked_ips = blocked_ips
                    self.approved_ips = [ip for ip, data in self.config_map["observed_ips"].items() if data["state"] == "approved"]

                #prof.disable()
                #s = io.StringIO()
                #stats = pstats.Stats(prof, stream=s).strip_dirs().sort_stats("cumtime")
                #stats.print_stats(100) # top 10 rows

                #runtime_end = time.time()
                #logging.info("RUNTIME: {} - {} IPs".format(runtime_end-runtime_start, len(ip_traffic_state)))
                #logging.info(s.getvalue())

                self.event.wait(60)

            logging.info("IP traffic blocker stopped")
        except Exception:
            logging.error(traceback.format_exc())
            self.is_running = False

    def _getHttpRequests(self):
        http_requests = {}
        try:
            start = datetime.now() - timedelta(seconds=self.config.traffic_blocker_unblock_timeout)
            query = "{{group=\"apache\"}} |= \" vhost={}:80 \" != \" status=200 \"".format(self.config.server_domain)
            url = "{}/loki/api/v1/query_range?start={}&query={}".format(self.config.loki_rest, start.timestamp(), urllib.parse.quote(query))
            contents = urllib.request.urlopen(url).read()
            result = json.loads(contents)
            external_state = {}
            if "status" in result and result["status"] == "success":
                for result in result["data"]["result"]:
                    for row in result["values"]:
                        #logging.info("{} {}".format(datetime.fromtimestamp(int(row[0]) / 1000000000), row[1]))
                        # message ${record["host"] + " - " + record["user"] + " - " + record["domain"] + " - " + record["request"] + " - " + record["code"] + " - " + record["message"]}
                        #                            IP         USER     DOMAIN   REQUEST
                        match = re.match("^remoteIP=([^\s]+).*?request=(.*?) status=",row[1])
                        if not match:
                            logging.error("Invalid regex for message: '{}'".format(row[1]))
                            continue

                        ip = match[1]

                        if ip in self.approved_ips:
                            continue

                        if ip not in external_state:
                            external_state[ip] = self.ipcache.isExternal(ipaddress.ip_address(ip))
                        if not external_state[ip]:
                            continue

                        request = match[2].strip('"')

                        match = re.match("^([A-Z]+) (.+) HTTP",request)
                        if not match:
                            is_suspicious = True
                            #logging.info("===============> Invalid IP: {}, REQUEST: {}".format(ip, request))
                        else:
                            method = match[1]
                            url = match[2]
                            #is_suspicious = method != "GET" or not re.match("^/(|.well-known|state|robots.txt|favicon.ico)$", url)
                            is_suspicious = method != "GET" or not re.match("^/(|favicon.ico)$", url)
                            #logging.info("===============> VALID IP: {}, METHOD: {}, URL: {}".format(ip, method, url))

                        #logging.info("===============> {} {}".format(ip, request))

                        time = datetime.fromtimestamp(int(row[0]) / 1000000000).timestamp()
                        if ip not in http_requests:
                            malware_type = self.malware.check(ip)
                            http_requests[ip] = { "count": 0, "type": malware_type if malware_type else "unknown", "details": TrafficGroup.SCANNING if malware_type else TrafficGroup.OBSERVED , "last": 0, "suspicious": False }
                        if not http_requests[ip]["suspicious"] and is_suspicious:
                            http_requests[ip]["suspicious"] = True
                            http_requests[ip]["details"] = TrafficGroup.SCANNING
                        if time > http_requests[ip]["last"]:
                            http_requests[ip]["last"] = time
                        http_requests[ip]["count"] += 1
        except urllib.error.HTTPError as e:
            logging.info(e)
            logging.info("Loki not reachable")

        #logging.info(str(http_requests))
        #return {}

        return http_requests

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
        return [
            "system_service_process{{type=\"trafficblocker\"}} {}".format("1" if self.is_running else "0"),
            "system_service_state{{type=\"trafficblocker\",details=\"cache_file\"}} {}".format("1" if self.valid_config_file else "0")
        ]
