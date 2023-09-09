import threading
import traceback
import logging
import re
import schedule
import time
from datetime import datetime

from smartserver import command

from lib.trafficwatcher.trafficblocker.trafficblocker import TrafficBlocker
from lib.trafficwatcher.netflowcollector.processor import Processor as NetflowProcessor, Connection as NetflowConnection
from lib.trafficwatcher.logcollector.logcollector import LogCollector, Connection as LogConnection
from lib.trafficwatcher.blocklists.blocklists import Blocklists

from lib.trafficwatcher.helper.helper import TrafficGroup, Helper as TrafficHelper

from lib.influxdb import InfluxDB
from lib.ipcache import IPCache

import cProfile as profile
import pstats
import io

WIREGUARD_PEER_TIMEOUT = 60 * 5 # 5 minutes

class Helper():
    __base32 = '0123456789bcdefghjkmnpqrstuvwxyz'

    @staticmethod
    def encodeGeohash(latitude, longitude, precision=12):
        lat_interval, lon_interval = (-90.0, 90.0), (-180.0, 180.0)
        geohash = []
        bits = [ 16, 8, 4, 2, 1 ]
        bit = 0
        ch = 0
        even = True
        while len(geohash) < precision:
            if even:
                mid = (lon_interval[0] + lon_interval[1]) / 2
                if longitude > mid:
                    ch |= bits[bit]
                    lon_interval = (mid, lon_interval[1])
                else:
                    lon_interval = (lon_interval[0], mid)
            else:
                mid = (lat_interval[0] + lat_interval[1]) / 2
                if latitude > mid:
                    ch |= bits[bit]
                    lat_interval = (mid, lat_interval[1])
                else:
                    lat_interval = (lat_interval[0], mid)
            even = not even
            if bit < 4:
                bit += 1
            else:
                geohash += Helper.__base32[ch]
                bit = 0
                ch = 0
        return ''.join(geohash)

    @staticmethod
    def getWireguardPeers():
        returncode, cmd_result = command.exec2(["/usr/bin/wg", "show"])
        if returncode != 0:
            raise Exception("Cmd '/usr/bin/wg show' was not successful")

        result = []
        for row in cmd_result.split("\n"):
            if "endpoint" not in row:
                continue
            match = re.match("^\s*endpoint: ([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}):.*",row)
            if match:
                result.append(match[1])

        #logging.info(str(result))
        return result

class TrafficWatcher(threading.Thread):
    def __init__(self, config, handler, influxdb, ipcache):
        threading.Thread.__init__(self)

        self.debugging_ips = []
        self.profiling_enabled = False

        self.influxdb = influxdb
        self.ipcache = ipcache

        self.event = threading.Event()

        self.blocklists = Blocklists(config, self.influxdb)
        self.netflow = NetflowProcessor(config, self, self.ipcache )
        self.logcollector = LogCollector(config, self, self.ipcache )

        self.trafficblocker = TrafficBlocker(config, self, self.influxdb, self.debugging_ips)

        self.config = config

        self.connections = []
        self.processed_connections = []

        self.stats = {"connections": 0, "suspicious": 0, "processing_time": 0}

        self.processed_flows = {}
        #self.last_metric_end = time.time() - METRIC_TIMESHIFT
        #self.suspicious_ips = {}

        self.traffic_metrics = {}
        self.ip_events = {}
        self.last_traffic_event = {}
        self.last_traffic_summery = None

        self.stats_lock = threading.Lock()

        self.wireguard_peers = {}
        self.allowed_isp_pattern = {}
        for target, data in config.netflow_incoming_traffic.items():
            self.allowed_isp_pattern[target] = {}
            for field, pattern in data["allowed"].items():
                self.allowed_isp_pattern[target][field] = re.compile(pattern, re.IGNORECASE)

    def start(self):
        self.is_running = True

        self.blocklists.start()
        self.netflow.start()

        self.trafficblocker.start()

        schedule.every().minute.at(":00").do(self._cleanTrafficState)
        self.influxdb.register(self.getMessurements)

        super().start()

    def terminate(self):
        self.is_running = False

        self.logcollector.terminate()

        self.trafficblocker.terminate()

        self.netflow.terminate()
        self.blocklists.terminate()

        self.event.set()

    def run(self):
        logging.info("Init traffic state")
        while self.is_running:
            try:
                self._initTrafficEvents()
                break
            except Exception as e:
                logging.info(e)
                #logging.info(traceback.format_exc())
                logging.info("InfluxDB not ready. Will retry in 15 seconds.")
                self.event.wait(15)

        if self.is_running:
            # must stay here, because it depends from initialized traffic state
            self.logcollector.start()

        logging.info("IP traffic watcher started")
        try:
            while self.is_running:
                self._processConnections()

                self.event.wait()
                self.event.clear()

            logging.info("IP traffic watcher stopped")
        except Exception:
            logging.error(traceback.format_exc())
            self.is_running = False

    def addConnections(self, connections):
        #logging.info("add {} {}".format(connection.connection_type, connection.src))
        for connection in connections:
            if connection.skipped:
                continue
            self.connections.append(connection)
        if self.connections:
            self.event.set()

    def _getWireguardPeers(self):
        now = time.time()

        _wireguard_peers = {}
        for wireguard_peer in Helper.getWireguardPeers():
            _wireguard_peers[wireguard_peer] = now

        for wireguard_peer in list(self.wireguard_peers.keys()):
            if wireguard_peer in _wireguard_peers:
                continue
            age = self.wireguard_peers[wireguard_peer]
            if age + WIREGUARD_PEER_TIMEOUT < now: # invalidate wireguard peer after 5 Minutes
                continue
            _wireguard_peers[wireguard_peer] = age

        #logging.info(str(self.wireguard_peers))
        #logging.info(str(_wireguard_peers))

        self.wireguard_peers = _wireguard_peers
        return self.wireguard_peers

    def _processConnections(self):
        start_processing = time.time()

        #if self.profiling_enabled:
        #    prof = profile.Profile()
        #    prof.enable()

        wireguard_peers = None
        connection_count = 0
        suspicious_ips = []

        while self.connections:
            con = self.connections.pop(0)

            _location = con.location
            if _location["type"] == IPCache.TYPE_LOCATION:
                location_country_name = _location["country_name"] if _location["country_name"] else "Unknown"
                location_country_code = _location["country_code"] if _location["country_code"] else "xx"
                location_zip = _location["zip"] if _location["zip"] else "0"
                location_city = _location["city"] if _location["city"] else "Unknown"
                #location_district = _location["district"] if _location["district"] else None
                location_geohash = Helper.encodeGeohash(_location["lat"], _location["lon"], 5) if _location["lat"] and _location["lon"] else None
                location_org = _location["org"] if _location["org"] else ( _location["isp"] if _location["isp"] else "Unknown" )
            elif _location["type"] == IPCache.TYPE_UNKNOWN:
                location_country_name = "Unknown"
                location_country_code = "xx"
                location_zip = "0"
                location_city = "Unknown"
                #location_district = None
                location_geohash = None
                location_org = "Unknown"
            elif _location["type"] == IPCache.TYPE_PRIVATE:
                location_country_name = "Private"
                location_country_code = "xx"
                location_zip = "0"
                location_city = "Private"
                #location_district = None
                location_geohash = None
                location_org = "Unknown"

            src_is_external = con.src_is_external
            extern_ip = str((con.src if src_is_external else con.dest).compressed)
            extern_hostname = con.src_hostname if src_is_external else con.dest_hostname
            intern_ip = str((con.dest if src_is_external else con.src).compressed)
            intern_hostname = con.dest_hostname if src_is_external else con.src_hostname

            if not self.trafficblocker.isApprovedIPs(extern_ip):
                blocklist_name = self.blocklists.check(extern_ip)
                if not blocklist_name and src_is_external and len(self.allowed_isp_pattern) > 0:
                    allowed = False
                    service_key = TrafficHelper.getServiceKey(con.dest, con.dest_port) if src_is_external else None
                    if service_key in self.allowed_isp_pattern:
                        if location_org and "org" in self.allowed_isp_pattern[service_key] and self.allowed_isp_pattern[service_key]["org"].match(location_org):
                            allowed = True
                        elif extern_hostname and "hostname" in self.allowed_isp_pattern[service_key] and self.allowed_isp_pattern[service_key]["hostname"].match(extern_hostname):
                            allowed = True
                        elif extern_ip:
                            if "ip" in self.allowed_isp_pattern[service_key] and self.allowed_isp_pattern[service_key]["ip"].match(extern_ip):
                                allowed = True
                            elif "wireguard_peers" in self.allowed_isp_pattern[service_key] and ( wireguard_peers is not None or ( wireguard_peers := self._getWireguardPeers() ) ) and extern_ip in wireguard_peers:
                                allowed = True
                                #logging.info("wireguard >>>>>>>>>>> {}".format(extern_ip))
                    if not allowed:
                        blocklist_name = "unknown"
                traffic_group = con.getTrafficGroup(blocklist_name)
            else:
                blocklist_name = None
                traffic_group = TrafficGroup.NORMAL

            if con.isFilteredTrafficGroup(traffic_group) and extern_ip not in self.debugging_ips:
                #logging.info("{} {}".format(extern_ip, "filtered"))
                continue

            direction = "incoming" if src_is_external else "outgoing"
            is_suspicious_traffic = traffic_group != "normal"
            is_scanning = con.connection_type == "netflow" and con.answer_flow is None and ( con.protocol_name == "udp" or con.tcp_flags == 2 ) # group unsuccessful syn requests

            if is_suspicious_traffic:
                with self.stats_lock:
                    self._addTrafficEvent(con.connection_type, extern_ip, traffic_group, blocklist_name, con.start_timestamp)
                suspicious_ips.append(extern_ip)

            if ( is_suspicious_traffic and not is_scanning and not self.trafficblocker.isBlockedIP(extern_ip) ) or extern_ip in self.debugging_ips:
                data = {
                    "type": con.connection_type,
                    "start": str(datetime.fromtimestamp(con.start_timestamp)),
                    "end": str(datetime.fromtimestamp(con.end_timestamp)),
                    "extern_ip": extern_ip,
                    "intern_ip": intern_ip,
                    "direction": direction,
                    "group": traffic_group
                }
                con.applyDebugFields(data)
                logging.info("Suspicious: {}".format(data))

            self.processed_connections.append({
                "location_country_name": location_country_name,
                "location_country_code": location_country_code,
                "location_zip": location_zip,
                "location_city": location_city,
                "location_geohash": location_geohash,
                "location_org": location_org,
                "extern_ip": extern_ip,
                "extern_hostname": extern_hostname,
                "intern_ip": intern_ip,
                "intern_hostname": intern_hostname,
                "direction": direction,
                "traffic_group": traffic_group,
                "blocklist_name": blocklist_name,
                "is_suspicious_traffic": is_suspicious_traffic,
                "is_scanning": is_scanning,
                "connection": con
            })

            self.stats["connections"] += 1

        suspicious_ips = list(set(suspicious_ips))

        end_processing = time.time()

        self.stats["processing_time"] += end_processing - start_processing

        #if self.profiling_enabled:
        #    prof.disable()
        #    s = io.StringIO()
        #    ps = pstats.Stats(prof, stream=s).strip_dirs().sort_stats("cumtime")
        #    ps.print_stats()
        #    logging.info(s.getvalue())

        #logging.info("Processing of {}/{} connections in {} seconds".format(len(suspicious_ips), connection_count, round(end_processing - start_processing,3)))

        if len(suspicious_ips) > 0:
            self.stats["suspicious"] += len(suspicious_ips)
            self.trafficblocker.triggerCheck(suspicious_ips)

    def _getProcessingStats(self):
        stats = self.stats
        self.stats = {"connections": 0, "suspicious": 0, "processing_time": 0}
        return stats

    def getTrafficStateSummery(self):
        now = time.strftime("%Y-%m-%d %H:%M")
        if self.last_traffic_summery is None or self.last_traffic_summery[1] != now:
            #start_time = time.time()
            count_values = {}
            results = self.influxdb.query('SELECT SUM("traffic_count") FROM "autogen"."trafficflow" WHERE time >= now() - 362m AND time <= now() - 2m AND "group"::tag != \'normal\' GROUP BY "group"::tag')
            if results is not None:
                for result in results:
                    count_values[result["tags"]["group"]] = result["values"][0][1]
            end_time = time.time()
            #logging.info(round(end_time-start_time, 3))
            #logging.info(results)
            self._fillTrafficGroups(count_values)
            self.last_traffic_summery = [ count_values, now ]

        return self.last_traffic_summery[0]

    def _initTrafficEvents(self):
        #logging.info("_initTrafficEvents")
        with self.stats_lock:
            # trafficevents,connection_type={},extern_ip={},traffic_group={}.blocklist_name={}
            results = self.influxdb.query('SELECT "connection_type","extern_ip","traffic_group","blocklist_name","value" FROM "trafficevents" WHERE time >= now() - 1440m') # => 24h
            #results = self.influxdb.query('SELECT "type","extern_ip","group","count" FROM "trafficflow" WHERE time >= now() - 358m AND "group"::tag != \'normal\'')
            if results is not None:
                for result in results:
                    for value in result["values"]:
                        #if value[3] > 1:
                        #    logging.info("{} {} {}".format(value[1], value[2], value[3]))
                        value_time = InfluxDB.parseDatetime(value[0])
                        self._addTrafficEvent(value[1], value[2], value[3], value[4], value_time.timestamp())

            self.traffic_metrics = {} # reset, will be used by prometheus metrics

    def _addTrafficEvent(self, connection_type, ip, traffic_group, blocklist_name, time):
        # lock is called in place where this function is called

        #logging.info("ADD {}".format(datetime.fromtimestamp(time)))
        if traffic_group not in self.traffic_metrics:
            self.traffic_metrics[traffic_group] = 0
        self.traffic_metrics[traffic_group] += 1

        if connection_type not in self.last_traffic_event or time > self.last_traffic_event[connection_type]:
            self.last_traffic_event[connection_type] = time

        if ip not in self.ip_events:
            self.ip_events[ip] = []

        self.ip_events[ip].append({"connection_type": connection_type, "traffic_group": traffic_group, "blocklist_name": blocklist_name, "time": time})

    def _cleanTrafficState(self):
        with self.stats_lock:
            min_time = time.time() - 60 * 60 * 24
            ip_events = {}
            for ip, events in self.ip_events.items():
                for data in events:
                    if data["time"] < min_time:
                        continue
                    if ip not in ip_events:
                        ip_events[ip] = []
                    ip_events[ip].append(data)
            self.ip_events = ip_events

    def _fillTrafficGroups(self, states):
        if "observed" not in states:
            states["observed"] = 0
        if "scanning" not in states:
            states["scanning"] = 0
        if "intruded" not in states:
            states["intruded"] = 0

    def getIPTrafficStates(self, ip_states):
        ipstates = {}
        with self.stats_lock:
            for ip, min_time in ip_states.items():
                for data in self.ip_events[ip]:
                    if min_time >= data["time"]:
                        continue

                    traffic_group = data["traffic_group"]
                    connection_type = data["connection_type"]

                    key = "{}_{}".format(connection_type, traffic_group)

                    if ip not in ipstates:
                        ipstates[ip] = {}
                    if key not in ipstates[ip]:
                        ipstates[ip][key] = {"count": 0, "connection_type": connection_type, "blocklist_name": data["blocklist_name"], "traffic_group": data["traffic_group"], "last": 0}
                    ipstates[ip][key]["count"] += 1
                    if data["time"] > ipstates[ip][key]["last"]:
                        ipstates[ip][key]["last"] = data["time"]
        #logging.info("getIPTrafficState: {}".format(ipstates))
        return ipstates

    def getLastTrafficEventTime(self, connection_type):
        with self.stats_lock:
            return self.last_traffic_event[connection_type] if connection_type in self.last_traffic_event else 0

    def getBlockedIPs(self):
        return self.trafficblocker.getBlockedIPs()

    def getObservedIPData(self):
        return self.trafficblocker.getObservedIPData()

    def getMessurements(self):
        messurements = []

        flows = {}

        while self.processed_connections:
            pc = self.processed_connections.pop(0)

            con = pc["connection"]

            intern_ip = pc["intern_ip"]
            extern_ip = pc["extern_ip"]
            traffic_group = pc["traffic_group"]
            blocklist_name = pc["blocklist_name"]
            is_suspicious_traffic = pc["is_suspicious_traffic"]
            direction = pc["direction"]

            is_blocked = self.trafficblocker.isBlockedIP(extern_ip)

            service = con.service

            if is_suspicious_traffic:
                messurements.append("trafficevents,connection_type={},extern_ip={},traffic_group={},blocklist_name={} value=1 {}".format(con.connection_type, extern_ip, traffic_group, blocklist_name, int(con.start_timestamp * 1000)))

            base_tags = {}
            state_tags = {}
            values = {}

            # group unsuccessful syn requests
            if pc["is_scanning"]:
                base_tags["destination_port"] = 0
                service = "scanning"
                time_offset = 5
            else:
                base_tags["destination_port"] = con.dest_port
                time_offset = 1
            #base_tags["destination_port"] = 0 if con.connection_type == "netflow" and con.tcp_flags & 2 == 2 and con.answer_flow is None else con.dest_port
            #base_tags["destination_port"] = con.dest_port

            base_tags["intern_ip"] = intern_ip
            base_tags["intern_host"] = pc["intern_hostname"]

            base_tags["extern_ip"] = extern_ip
            base_tags["extern_host"] = pc["extern_hostname"]
            extern_group = pc["extern_hostname"]
            m = re.search('^.*?([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+|[a-z0-9-]+\.[a-z0-9]+)$', extern_group)
            if m and m.group(1) != extern_group:
                extern_group = "*.{}".format(m.group(1))
            base_tags["extern_group"] = extern_group

            base_tags["service"] = service

            base_tags["direction"] = direction
            base_tags["protocol"] = con.protocol_name

            base_tags["ip_type"] = con.ip_type

            base_tags["location_country_name"] = pc["location_country_name"]
            base_tags["location_country_code"] = pc["location_country_code"]
            base_tags["location_zip"] = pc["location_zip"]
            base_tags["location_city"] = pc["location_city"]
            if pc["location_org"]:
                base_tags["location_org"] = pc["location_org"]

            if pc["location_geohash"]:
                values["location_geohash"] = pc["location_geohash"]
                base_tags["location_has_geohash"] = 1

            values["blocked"] = 1 if is_blocked else 0

            base_tags_r = []
            for name, value in base_tags.items():
                base_tags_r.append(str(value))
            key = ",".join(base_tags_r)

            # dummy values needed for a propper delete query
            state_tags["group"] = "-"
            state_tags["traffic_group"] = "-"
            state_tags["log_group"] = "-"
            state_tags["log_type"] = "-"

            #values["traffic_size"] = 0
            #values["traffic_count"] = 0
            #values["tcp_flags"] = 0

            #values["log_count"] = 0

            if extern_ip in self.debugging_ips:
                is_debug = True
                logging.info(key)
            else:
                is_debug = is_suspicious_traffic

            # **** COLLECT MERGABLE FLOWS ****
            related_flows = []
            if key in flows:
                for flow in list(flows[key]):
                    start = flow["start_timestamp"] - time_offset
                    end = flow["end_timestamp"] + time_offset
                    if ( con.start_timestamp > start and con.start_timestamp < end ) or ( con.end_timestamp > start and con.end_timestamp < end ) or ( con.start_timestamp < start and con.end_timestamp > end ):
                        if is_debug:
                            logging.info("Apply to registry - Type: {}, IP: {}, Time: {}".format(con.connection_type, extern_ip, str(datetime.fromtimestamp(flow["start_timestamp"]))))
                        related_flows.append(flow)
                        flows[key].remove(flow)
            else:
                flows[key] = []

            processed_related_flows = []
            if key in self.processed_flows:
                for flow in list(self.processed_flows[key]):
                    start = flow["start_timestamp"] - time_offset
                    end = flow["end_timestamp"] + time_offset
                    if ( con.start_timestamp > start and con.start_timestamp < end ) or ( con.end_timestamp > start and con.end_timestamp < end ) or ( con.start_timestamp < start and con.end_timestamp > end ):
                        if is_debug:
                            logging.info("Apply to last registry - Type: {}, IP: {}, Time: {}".format(con.connection_type, extern_ip, str(datetime.fromtimestamp(flow["start_timestamp"]))))
                        processed_related_flows.append(flow)
                        self.processed_flows[key].remove(flow)
            else:
                self.processed_flows[key] = []
            # *********************************

            # **** MERGE FLOWS ****
            data = { "key": key, "base_tags": base_tags, "state_tags": state_tags, "values": values, "start_timestamp": con.start_timestamp, "end_timestamp": con.end_timestamp, "influxdb_timestamp": 0, "processed_related_flows": processed_related_flows, "query": None}
            con.applyData(data, traffic_group)
            flows[key].append(data)

            related_flows += processed_related_flows
            for flow in related_flows:
                NetflowConnection.mergeData(data, flow)
                LogConnection.mergeData(data, flow)

                if flow["start_timestamp"] < data["start_timestamp"]:
                    data["start_timestamp"] = flow["start_timestamp"]

                if flow["end_timestamp"] > data["end_timestamp"]:
                    data["end_timestamp"] = flow["end_timestamp"]

                data["processed_related_flows"] += flow["processed_related_flows"]

            data["influxdb_timestamp"] = int(data["start_timestamp"]) * 1000
            data["values"]["duration"] = data["end_timestamp"] - data["start_timestamp"]
            # ********************

        flow_values = []
        for _flow_values in flows.values():
            flow_values += _flow_values

        # **** CREATE MESSUREMENTS ****
        cleanup_messurements = []
        sorted_flow_values = sorted(flow_values, key=lambda x: ["influxdb_timestamp"])
        for flow in sorted_flow_values:
            tags = flow["base_tags"] | flow["state_tags"]

            tag_str_r = []
            for name, value in tags.items():
                if isinstance(value, str):
                    tag_str_r.append("{}={}".format(name,InfluxDB.escapeTagValue(value)))
                else:
                    tag_str_r.append("{}={}".format(name,value))
            tag_str = ",".join(tag_str_r)

            values_r = []
            for name,value in flow["values"].items():
                if isinstance(value, list):
                    values_r.append("{}=\"{}\"".format(name,value[1](value[0])))
                elif isinstance(value, str):
                    values_r.append("{}=\"{}\"".format(name,InfluxDB.escapeFieldValue(value)))
                else:
                    values_r.append("{}={}".format(name,value))
            value_str = ",".join(values_r)

            # **** PREPARE CLEANUP RELATED FLOWS => DELETE if tags or timestamp has changed ****
            for processed_related_flow in flow["processed_related_flows"]:
                # skip messurements with equal tags and timestamp, they will be replaced with the following update
                if processed_related_flow["query"][1] == tag_str and processed_related_flow["influxdb_timestamp"] == flow["influxdb_timestamp"]:
                    #if flow["state_tags"]["group"] != "normal":
                    #    logging.info("==========================")
                    #    logging.info(processed_related_flow["query"][1])
                    #    logging.info(tag_str)
                    #    logging.info(processed_related_flow["influxdb_timestamp"])
                    #    logging.info(flow["influxdb_timestamp"])
                    continue
                #logging.info("CLEANUP => OLD TAGS: {}".format(flow["query"][1]))
                #logging.info("CLEANUP => NEW TAGS: {}".format(tag_str))
                cleanup_messurements.append(["trafficflow", processed_related_flow["query"][0], processed_related_flow["influxdb_timestamp"]])
            # **********************************************************************************

            messurements.append("trafficflow,{} {} {}".format(tag_str, value_str, flow["influxdb_timestamp"]))

            flow["processed_related_flows"] = []
            flow["query"] = [ tags, tag_str ]
            self.processed_flows[flow["key"]].append(flow)
        # ******************************

        # **** DELETE OBSOLETE RELATED FLOWS ****
        if len(cleanup_messurements) > 0:
            #start_cleanup = time.time()

            queries = []
            for messurement, tags, timestamp in cleanup_messurements:
                tag_r = []
                for name, value in tags.items():
                    if isinstance(value, str):
                        tag_r.append("\"{}\"='{}'".format(name,value.replace("'","\\'")))
                    else:
                        tag_r.append("\"{}\"='{}'".format(name,value))
                tag_str = " AND ".join(tag_r)
                queries.append("DELETE FROM \"{}\" WHERE {} AND \"time\" = {}".format(messurement, tag_str, (timestamp * 1000000) ))

            result = self.influxdb.delete(queries)

            #end_cleanup = time.time()
            #logging.info(queries)
            #logging.info("Delete of {} messurements in {} seconds".format( len(cleanup_messurements), round(end_cleanup-start_cleanup,3)))
        # *******************************

        #start_cleanup = time.time()
        max_time = time.time() - 60 * 5
        flow_count = 0
        flow_cleanup_count = 0
        for key in list(self.processed_flows.keys()):
            for _data in list(self.processed_flows[key]):
                flow_count += 1
                if _data["end_timestamp"] >= max_time:
                    continue
                self.processed_flows[key].remove(_data)
                flow_cleanup_count += 1
            if len(self.processed_flows[key]) == 0:
                del self.processed_flows[key]

        #end_cleanup = time.time()
        #logging.info("Cleanup of {}/{} flows in {} seconds".format(flow_cleanup_count, flow_count, round(end_cleanup - start_cleanup,3)))

        counter_values = self.ipcache.getCountStats()
        cache_stats = "LOCATION [fetch: {}, cache {}/{}], HOSTNAME [fetch: {}, cache {}/{}]".format(counter_values["location_fetch"], counter_values["location_cache"], self.ipcache.getLocationSize(), counter_values["hostname_fetch"], counter_values["hostname_cache"], self.ipcache.getHostnameSize())
        processing_values = self._getProcessingStats()
        processing_stats = "Processing of {}/{} connections in {} seconds.".format(processing_values["suspicious"], processing_values["connections"], round(processing_values["processing_time"],3))
        logging.info("{} {}".format(processing_stats, cache_stats))

        return messurements

    def getStateMetrics(self):
        metrics = ["system_service_process{{type=\"trafficwatcher\"}} {}".format("1" if self.is_running else "0")]

        with self.stats_lock:
            count_values = self.traffic_metrics.copy()
            self.traffic_metrics = {}

        self._fillTrafficGroups(count_values)
        for group, count in count_values.items():
            metrics.append( "system_service_trafficwatcher{{type=\"{}\",}} {}".format( group, count ) )

        metrics = metrics + self.logcollector.getStateMetrics()
        metrics = metrics + self.netflow.getStateMetrics()
        metrics = metrics + self.blocklists.getStateMetrics()
        metrics = metrics + self.trafficblocker.getStateMetrics()

        return metrics
