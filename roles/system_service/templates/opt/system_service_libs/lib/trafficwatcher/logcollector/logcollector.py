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
import websocket

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

    def getDebugData(self):
        return ""

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

        self.timer = None

        server_ports = []
        for service in self.config.netflow_incoming_traffic:
            if self.config.netflow_incoming_traffic[service]["logs"] != "apache":
                continue
            ip, port = service.split(":")
            if ip != self.config.server_ip:
                continue
            server_ports.append(port)

        #self.query_test = "{group=\"apache\"}"
        self.query = "{{group=\"apache\"}} |~ \" vhost={}:({}) \" != \" status=200 \"".format(self.config.server_domain, "|".join(server_ports)) if len(server_ports) > 0 else None
        self.limit = 10000

        self.starttime = None

        self.ws = None

    def start(self):
        if self.query is not None:
            self.is_running = True
            super().start()
        else:
            logging.info("IP log collector disabled. There are is no 'netflow_incoming_traffic' with a 'log' attribute configured.")

    def terminate(self):
        if self.query is not None:
            self.is_running = False
            if self.ws is not None:
                self.ws.close()
            if self.timer is not None:
                self.timer.cancel()
            self.event.set()

    def run(self):
        logging.info("Log collector started")
        try:
            while self.is_running:
                self.timer = threading.Timer(60 * 60 * 24, self._force_reconnect)
                self.timer.start()

                self._connect()

                if self.ws is None:
                    continue

                self.event.wait(15)
        except Exception as e:
            #logging.error(e)
            logging.error(traceback.format_exc())
            self.is_running = False

        logging.info("Log collector stopped")

    def _force_reconnect(self):
        if self.ws is not None:
            logging.info("Log stream forced to reconnect")
            self.ws.close()
            self.ws = None

    def _connect(self):
        now = time.time()
        self.starttime = self.watcher.getLastTrafficEventTime("apache")
        #logging.info(start)
        if self.starttime == 0:
            self.starttime = now - self.watcher.getTrafficEventTimeslot()
        else:
            self.starttime += 0.001

        #url = "{}/loki/api/v1/tail?query={}".format(self.config.loki_websocket, urllib.parse.quote(self.query_test))
        url = "{}/loki/api/v1/tail?start={}&limit={}&query={}".format(self.config.loki_websocket, self.starttime, self.limit, urllib.parse.quote(self.query))
        #logging.info(url)
        #handler = logging.getLogger('logcollector')
        #websocket.enableTrace(True, handler = handler )

        self.ws = websocket.WebSocketApp(url, on_open=self._on_open, on_close=self._on_close, on_error=self._on_error, on_message=self._on_message)
        self.ws.run_forever(ping_interval=5, ping_timeout=1, reconnect=5)

    def _on_open(self, ws):
        logging.info("Log stream started at {}".format(datetime.fromtimestamp(self.starttime)))

    def _on_close(self, ws, close_status_code, close_message):
        if self.ws is None:
            return
        logging.info("Log stream closed with status: {}, message: {}".format(close_status_code, close_message))

    def _on_error(self, ws, error):
        if self.ws is None:
            return
        logging.error("Log stream got error {}".format(error))

    def _on_message(self, ws, message):
        #logging.info("on message {}".format(message))

        try:
            message = json.loads(message)

            all_events = 0
            connections = []
            for result in message["streams"]:
                for row in result["values"]:
                    all_events += 1

                    timestamp = int(row[0]) / 1000000000

                    #logging.info("{} {}".format(datetime.fromtimestamp(int(row[0]) / 1000000000), row[1]))
                    # message ${record["host"] + " - " + record["user"] + " - " + record["domain"] + " - " + record["request"] + " - " + record["code"] + " - " + record["message"]}
                    #                            IP         USER     DOMAIN   REQUEST
                    match = re.match("^remoteIP=([^\s]+).*?vhost=(.*?) request=(.*?) status=",row[1])
                    if not match:
                        logging.error("Invalid regex for message: '{}'".format(row[1]))
                        continue

                    ip = match[1]

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

                    connections.append(Connection(timestamp, self.config.server_ip, port, ip, is_suspicious, self.config, self.ipcache))
            self.watcher.addConnections(connections)

            if all_events == self.limit:
                logging.error("Loki query limit of {} reached".format(self.limit))
        except Exception as e:
            #logging.error(e)
            logging.error(traceback.format_exc())

    def getStateMetrics(self):
        return [ "system_service_process{{type=\"trafficwatcher.logcollector\"}} {}".format("1" if self.is_running else ( "-1" if self.ws is None else "0" )) ]
