import threading
import traceback
import logging
import time
import schedule
import os
import math
from datetime import datetime, timedelta

import cProfile as profile
import pstats
import io

from smartserver.confighelper import ConfigHelper

from lib.trafficwatcher.trafficblocker.helper import Helper
from lib.trafficwatcher.helper.helper import TrafficGroup


class TrafficBlocker(threading.Thread):
    def __init__(self, config, watcher, influxdb, debugging_ips):
        threading.Thread.__init__(self)

        self.profiling_enabled = False

        self.config = config
        self.watcher = watcher

        self.is_running = False

        self.event = threading.Event()

        self.config_lock = threading.Lock()

        self.dump_config_path = "/var/lib/system_service/trafficblocker.json"
        self.config_version = 3
        self.valid_config_file = True
        self.config_map = None

        self.blocked_ips = []
        self.approved_ips = []
        self.debugging_ips = debugging_ips

        self.influxdb = influxdb

        self._restore()

    def start(self):
        if self.config.traffic_blocker_enabled:
            self.is_running = True

            schedule.every().day.at("01:00").do(self._dump)
            schedule.every().hour.at("00:00").do(self._cleanup)
            self.influxdb.register(self.getMessurements)

            super().start()
        else:
            logging.info("IP traffic blocker disabled. Either it is completely deactivated by the variable 'traffic blocker' or no 'netflow_incoming_traffic' is configured.")

    def terminate(self):
        if self.config.traffic_blocker_enabled:
            if self.is_running and os.path.exists(self.dump_config_path):
                self._dump()
            self.is_running = False
            self.event.set()

    def run(self):
        logging.info("IP traffic blocker started")
        try:
            self.blocked_ips = Helper.getBlockedIps()

            HIERARCHY = {
                TrafficGroup.SCANNING: [TrafficGroup.INTRUDED],
                TrafficGroup.OBSERVED: [TrafficGroup.SCANNING, TrafficGroup.INTRUDED]
            }

            while self.is_running:
                #runtime_start = time.time()
                #prof = profile.Profile()
                #prof.enable()

                self.event.wait()
                self.event.clear()
                if not self.is_running:
                    break

                start_processing = time.time()

                if self.profiling_enabled:
                    prof = profile.Profile()
                    prof.enable()

                observed_ip_states = {ip: data["last"] for ip, data in self.config_map["observed_ips"].items()}

                now = time.time()
                blocked_ips = Helper.getBlockedIps()
                ip_traffic_state, total_events = self.watcher.getIPTrafficStates(observed_ip_states)
                #logging.info(ip_traffic_state)

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
                for ip, groups in ip_traffic_state.items():
                    if len(groups) == 1:
                        continue
                    for group_key, group_data in groups.items():
                        if group_data["traffic_group"] not in HIERARCHY:
                            continue
                        for sub_group in HIERARCHY[group_data["traffic_group"]]:
                            for _group_data in groups.values():
                                if group_data["connection_type"] == _group_data["connection_type"] and sub_group == _group_data["traffic_group"]:
                                    group_data["count"] += _group_data["count"]
                                    break

                # restore state
                for ip in [ip for ip, data in self.config_map["observed_ips"].items() if data["state"] == "blocked" and ip not in blocked_ips]:
                    Helper.blockIp(ip)
                    blocked_ips.append(ip)
                    logging.info("BLOCK IP {} restored for state: blocked".format(ip))

                with self.config_lock:
                    for ip, groups in ip_traffic_state.items():
                        #logging.info("===> {} {}".format(ip, groups))

                        if ip in self.config_map["observed_ips"]:
                            data = self.config_map["observed_ips"][ip]
                            if data["state"] == "approved": # unblock validated ip
                                continue

                            for group_key, group_data in groups.items():
                                if group_data["last"] > data["last"]:
                                    data["last"] = group_data["last"]

                            if data["state"] == "blocked":
                                continue

                        for group_key, group_data in groups.items():
                            #logging.info("{} {} {} {}".format(ip, group_key, group_data["count"], datetime.fromtimestamp(group_data["last"])))
                            #logging.info("{} {} {} {}".format(group_key, group_data["connection_type"], group_data["type"], group_data["details"]))

                            treshold = self.config.traffic_blocker_treshold[group_key]
                            if ip in self.config_map["observed_ips"]:
                                treshold = math.ceil( treshold / ( data["count"] + 1 ) ) # calculate treshhold based on number of blocked periods

                            if group_data["count"] > treshold:
                                if ip in self.config_map["observed_ips"]:
                                    data = self.config_map["observed_ips"][ip]
                                    data["updated"] = now
                                    data["state"] = "blocked"
                                    data["reason"] = group_data["connection_type"]
                                    data["blocklist"] = group_data["blocklist_name"]
                                    data["group"] = group_data["traffic_group"]
                                    if ip not in blocked_ips:
                                        data["count"] += 1
                                else:
                                    self.config_map["observed_ips"][ip] = {
                                        "created": now,
                                        "updated": now,
                                        "last": group_data["last"],
                                        "count": 1,
                                        "state": "blocked",
                                        "reason": group_data["connection_type"],
                                        "blocklist": group_data["blocklist_name"],
                                        "group": group_data["traffic_group"]
                                    }

                                if ip not in blocked_ips:
                                    Helper.blockIp(ip)
                                    blocked_ips.append(ip)
                                    logging.info("BLOCK IP {} after {} samples ({} - {} - {})".format(ip, group_data["count"], group_data["connection_type"], group_data["blocklist_name"], group_data["traffic_group"]))

                                break

                    for ip in blocked_ips:
                        if ip in self.config_map["observed_ips"]:
                            data = self.config_map["observed_ips"][ip]
                            if data["state"] == "blocked":
                                if ip in ip_traffic_state:
                                    continue
                                factor = pow(3,data["count"] - 1)
                                if factor > 168: # => 24h * 7d
                                    factor = 168
                                # 3 ^ 0 => 1, 1 => 3, 2 => 9, 3 => 27
                                time_offset = data["last"] + ( 3600 * factor ) # 60sec * 60min => 3600
                                if now <= time_offset:
                                    continue
                                data["updated"] = now
                                data["state"] = "unblocked"
                                logging.info("UNBLOCK IP {} after {}".format(ip, timedelta(seconds=(now - data["last"]))))
                            else:
                                logging.info("UNBLOCK IP {} restored for state: {}".format(ip, data["state"]))
                        else:
                            logging.info("UNBLOCK IP {} restored for missing state".format(ip))

                        Helper.unblockIp(ip)
                        blocked_ips.remove(ip)


                    self.blocked_ips = blocked_ips
                    self.approved_ips = [ip for ip, data in self.config_map["observed_ips"].items() if data["state"] == "approved"]

                end_processing = time.time()
                logging.info("Processing of {} ip's from {} traffic events in {} seconds".format(len(ip_traffic_state), total_events, round(end_processing - start_processing,3)))

                if self.profiling_enabled:
                    prof.disable()
                    s = io.StringIO()
                    ps = pstats.Stats(prof, stream=s).strip_dirs().sort_stats("cumtime")
                    ps.print_stats()
                    logging.info(s.getvalue())

            logging.info("IP traffic blocker stopped")
        except Exception:
            logging.error(traceback.format_exc())
            self.is_running = False

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
        max_age = 60 * 60 * 24 * 14
        cleaned = 0
        with self.config_lock:
            for ip in list(self.config_map["observed_ips"].keys()):
                data = self.config_map["observed_ips"][ip]
                if data["state"] != "unblocked" or now < data["updated"] + max_age:
                    continue
                del self.config_map["observed_ips"][ip]
                cleaned = cleaned + 1
        if cleaned > 0:
            logging.info("Cleaned {} ip(s)".format(cleaned))

    def triggerCheck(self):
        self.event.set()

    def isApprovedIPs(self, ip):
        if ip in self.debugging_ips:
            return True
        return ip in self.approved_ips

    def isBlockedIP(self, ip):
        return ip in self.blocked_ips

    def getBlockedIPs(self):
        return list(self.blocked_ips)

    def getObservedIPData(self):
        observed_ips = []
        with self.config_lock:
            for ip, data in self.config_map["observed_ips"].items():
                data = data.copy()
                data["ip"] = ip
                observed_ips.append(data)
        return observed_ips

    def getMessurements(self):
        messurements = []
        if self.config_map is not None:
            with self.config_lock:
                for ip, data in self.config_map["observed_ips"].items():
                    if data["state"] != "blocked":
                        continue
                    messurements.append("trafficblocker,extern_ip={},blocking_state={},blocking_reason={},blocking_list={},blocking_count={} value=\"{}\"".format(ip, data["state"], data["reason"], data["blocklist"], data["count"], data["last"]))
        return messurements

    def getStateMetrics(self):
        return [
            "system_service_process{{type=\"trafficwatcher.trafficblocker\"}} {}".format("1" if self.is_running else "0"),
            "system_service_state{{type=\"trafficwatcher.trafficblocker\",details=\"cache_file\"}} {}".format("1" if self.valid_config_file else "0")
        ]
