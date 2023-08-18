import threading
import traceback
import logging
import time
import schedule
import os
import math
import datetime

from smartserver.confighelper import ConfigHelper

from lib.trafficblocker.helper import Helper


class TrafficBlocker(threading.Thread):
    def __init__(self, config, handler, influxdb, netflow):
        threading.Thread.__init__(self)

        self.config = config
        self.netflow = netflow

        self.is_running = False

        self.event = threading.Event()

        self.config_lock = threading.Lock()

        self.dump_config_path = "/var/lib/system_service/trafficblocker.json"
        self.config_version = 1
        self.valid_config_file = True
        self.config_map = None

        self.blocked_ips = []

        self.influxdb = influxdb

    def start(self):
        self.is_running = True
        self._restore()

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
            if self.config_map is None:
                self.config_map = {"observed_ips": {}}
                if self.valid_config_file:
                    self._dump()

            self.blocked_ips = []

            while self.is_running:
                now = time.time()
                blocked_ips = Helper.getBlockedIps()
                attackers = self.netflow.getAttackers()
                attacking_ips = []

                with self.config_lock:
                    for attacker in attackers:
                        ip = attacker["ip"]
                        attacking_ips.append(ip)

                        treshold = self.config.traffic_blocker_treshold[attacker["group"]]
                        if ip in self.config_map["observed_ips"]:
                            if self.config_map["observed_ips"][ip]["state"] == "approved": # unblock validated ip
                                if ip in blocked_ips:
                                    Helper.unblockIp(ip)
                                    blocked_ips.remove(ip)
                                    logging.info("UNBLOCK IP {} forced".format(ip))
                                continue

                            self.config_map["observed_ips"][ip]["updated"] = now
                            if self.config_map["observed_ips"][ip]["state"] == "blocked": # restore state
                                if ip not in blocked_ips:
                                    logging.info("BLOCK IP {} restored".format(ip))
                                    Helper.blockIp(ip)
                                    blocked_ips.append(ip)
                                continue
                            treshold = math.ceil( treshold / ( self.config_map["observed_ips"][ip]["count"] + 1 ) ) # calculate treshhold based on number of blocked periods

                        if attacker["count"] > treshold or ip in blocked_ips:
                            if ip in self.config_map["observed_ips"]:
                                self.config_map["observed_ips"][ip]["state"] = "blocked"
                                self.config_map["observed_ips"][ip]["count"] += 1
                            else:
                                self.config_map["observed_ips"][ip] = { "created": now, "updated": now, "count": 1, "state": "blocked" }

                            if ip not in blocked_ips:
                                logging.info("BLOCK IP {} after {} requests".format(ip, treshold))
                                Helper.blockIp(ip)
                                blocked_ips.append(ip)

                    for ip in [ip for ip in blocked_ips if ip not in attacking_ips]:
                        if ip in self.config_map["observed_ips"]:
                            data = self.config_map["observed_ips"][ip]
                            factor = 0 if data["count"] <= 1 else pow(2,data["count"] - 2)
                            time_offset = data["updated"] + ( self.config.traffic_blocker_unblock_timeout * factor )
                            if now <= time_offset:
                                continue
                            logging.info("UNBLOCK IP {} after {}".format(ip, datetime.timedelta(seconds=(now - time_offset))))
                            data["updated"] = now
                            data["state"] = "unblocked"
                        else:
                            logging.info("UNBLOCK IP {}".format(ip))
                        Helper.unblockIp(ip)
                        blocked_ips.remove(ip)

                    self.blocked_ips = blocked_ips

                self.event.wait(60)

            logging.info("IP traffic blocker stopped")
        except Exception:
            logging.error(traceback.format_exc())
            self.is_running = False

    def _restore(self):
        self.valid_list_file, data = ConfigHelper.loadConfig(self.dump_config_path, self.config_version )
        if data is not None:
            self.config_map = data["map"]
            logging.info("Loaded config")

    def _dump(self):
        with self.config_lock:
            ConfigHelper.saveConfig(self.dump_config_path, self.config_version, { "map": self.config_map } )
            logging.info("Saved config")

    def _cleanup(self):
        now = time.time()
        cleaned = 0
        for ip in list(self.config_map["observed_ips"].keys()):
            data = self.config_map["observed_ips"][ip]
            if data["state"] != "unblocked" or now < data["updated"] + self.config.traffic_blocker_clean_known_ips_timeout:
                continue
            del self.config_map["observed_ips"][ip]
            cleaned = cleaned + 1
        if cleaned > 0:
            logging.info("Cleaned {} ip(s)".format(cleaned))

    def getApprovedIPs(self):
        return [ip for ip, data in self.config_map["observed_ips"].items() if data["state"] == "approved"]

    def getBlockedIPs(self):
        return list(self.blocked_ips)

    def getMessurements(self):
        messurements = []
        if self.config_map is not None:
            with self.config_lock:
                for ip, data in self.config_map["observed_ips"].items():
                    messurements.append("trafficblocker,extern_ip={},blocked_state={}  value=\"{}\"".format(ip, data["state"], data["count"]))
        return messurements

    def getStateMetrics(self):
        return [
            "system_service_process{{type=\"trafficblocker\",}} {}".format("1" if self.is_running else "0"),
        ]
