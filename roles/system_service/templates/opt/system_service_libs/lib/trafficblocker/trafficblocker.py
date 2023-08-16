import threading
import traceback
import logging
import time

from smartserver.confighelper import ConfigHelper

from lib.trafficblocker.helper import Helper


class TrafficBlocker(threading.Thread):
    def __init__(self, config, handler, netflow):
        threading.Thread.__init__(self)

        self.config = config
        self.netflow = netflow

        self.is_running = False

        self.event = threading.Event()

        #self.dump_config_path = "/var/lib/system_service/trafficblocker.json"
        #self.config_version = 1
        #self.valid_config_file = True
        #self.config_map = None

        self.blocked_ips = []

    def start(self):
        self.is_running = True
        #self._restore()
        super().start()

    def terminate(self):
        self.is_running = False
        self.event.set()

    def run(self):
        logging.info("IP attack blocker started")
        try:
            #if self.config_map is None:
            #    self.config_map = {}#{"blocked_ips": {}}
            #    if self.valid_config_file:
            #        self._dump()

            while self.is_running:
                blocked_ips = Helper.getBlockedIps()
                attackers = self.netflow.getAttackers()
                self.blocked_ips = []
                for attacker in attackers:
                    if attacker["count"] > self.config.traffic_blocker_treshold[attacker["group"]]:
                        self.blocked_ips.append(attacker["ip"])
                        if attacker["ip"] not in blocked_ips:
                            Helper.blockIp(attacker["ip"])
                for blocked_ip in blocked_ips:
                    if blocked_ip not in self.blocked_ips:
                        Helper.unblockIp(blocked_ip)

                self.event.wait(60)

            logging.info("IP attack blocker stopped")
        except Exception:
            logging.error(traceback.format_exc())
            self.is_running = False

    #def _restore(self):
    #    self.valid_list_file, data = ConfigHelper.loadConfig(self.dump_config_path, self.config_version )
    #    if data is not None:
    #        self.config_map = data["map"]
    #        logging.info("Loaded config")

    #def _dump(self):
    #    ConfigHelper.saveConfig(self.dump_config_path, self.config_version, { "map": self.config_map } )
    #    logging.info("Saved config")

    def getBlockedIPs(self):
        return list(self.blocked_ips)

    def getStateMetrics(self):
        return [
            "system_service_process{{type=\"trafficblocker\",}} {}".format("1" if self.is_running else "0"),
        ]
