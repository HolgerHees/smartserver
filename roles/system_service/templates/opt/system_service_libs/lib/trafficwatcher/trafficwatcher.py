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

from lib.trafficwatcher.helper.trafficgroup import TrafficGroup

from lib.influxdb import InfluxDB
from lib.ipcache import IPCache


WIREGUARD_PEER_TIMEOUT = 60 * 5 # 5 minutes

class Helper():
    __base32 = '0123456789bcdefghjkmnpqrstuvwxyz'

    @staticmethod
    def getServiceKey(ip, port):
        return "{}:{}".format(ip.compressed, port)

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

        self.influxdb = influxdb
        self.ipcache = ipcache

        self.event = threading.Event()

        self.blocklists = Blocklists(config, self.influxdb)
        self.netflow = NetflowProcessor(config, self, self.ipcache )
        self.logcollector = LogCollector(config, self, self.ipcache )

        self.trafficblocker = TrafficBlocker(config, self, self.influxdb)

        self.config = config

        self.connections = []
        self.last_registry = {}
        #self.last_metric_end = time.time() - METRIC_TIMESHIFT
        #self.suspicious_ips = {}

        self.ip_stats = []
        self.traffic_stats = {}
        self.last_traffic_stats = {}

        self.stats_lock = threading.Lock()

        self.last_processed_traffic_stats = 0

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
        while True:
            try:
                self._initTrafficState()
                break
            except Exception as e:
                logging.info(e)
                #logging.info(traceback.format_exc())
                logging.info("InfluxDB not ready. Will retry in 15 seconds.")
                time.sleep(15)

        # must stay here, because it depends from initialized traffic state
        self.logcollector.start()

        logging.info("IP traffic watcher started")
        try:
            while self.is_running:
                self.event.wait(60)

            logging.info("IP traffic watcher stopped")
        except Exception:
            logging.error(traceback.format_exc())
            self.is_running = False

    def addConnection(self, connection):
        #logging.info("add {} {}".format(connection.connection_type, connection.src))
        self.connections.append(connection)

    def _cleanTrafficState(self):
        with self.stats_lock:
            min_time = time.time() - 60 * 60 * 6

            for group in list(self.traffic_stats.keys()):
                values = [time for time in self.traffic_stats[group] if time > min_time]
                if len(values) == 0:
                    del self.traffic_stats[group]
                else:
                    self.traffic_stats[group] = values

            self.ip_stats = [data for data in self.ip_stats if data["time"] > min_time]

    def _initTrafficState(self):
        #logging.info("_initTrafficState")
        with self.stats_lock:
            # 362 min => 6h - 2 min
            # trafficevents,connection_type={},extern_ip={},traffic_group={}.blocklist_name={}
            results = self.influxdb.query('SELECT "connection_type","extern_ip","traffic_group","blocklist_name","value" FROM "trafficevents" WHERE time >= now() - 358m')
            #results = self.influxdb.query('SELECT "type","extern_ip","group","count" FROM "trafficflow" WHERE time >= now() - 358m AND "group"::tag != \'normal\'')
            self.traffic_stats = {}
            if results is not None:
                for result in results:
                    for value in result["values"]:
                        #if value[3] > 1:
                        #    logging.info("{} {} {}".format(value[1], value[2], value[3]))
                        value_time = InfluxDB.parseDatetime(value[0])
                        self._addTrafficState(value[1], value[2], value[3], value[4], value_time.timestamp())
            self.last_processed_traffic_stats = max(self.last_traffic_stats.values()) if len(self.last_traffic_stats) > 0 else 0

            #logging.info(self.traffic_stats)
            #logging.info(self.last_traffic_stats)
            #logging.info("======================>")
            #logging.info(self.last_processed_traffic_stats)

    def _addTrafficState(self, connection_type, ip, traffic_group, blocklist_name, time):
        # lock is called in place where this function is called

        #logging.info("ADD {}".format(datetime.fromtimestamp(time)))
        if traffic_group not in self.traffic_stats:
            self.traffic_stats[traffic_group] = []
        self.traffic_stats[traffic_group].append(time)
        if connection_type not in self.last_traffic_stats or time > self.last_traffic_stats[connection_type]:
            self.last_traffic_stats[connection_type] = time

        self.ip_stats.append({"ip": ip, "connection_type": connection_type, "traffic_group": traffic_group, "blocklist_name": blocklist_name, "time": time})

    def _fillTrafficStates(self, states):
        if "observed" not in states:
            states["observed"] = 0
        if "scanning" not in states:
            states["scanning"] = 0
        if "intruded" not in states:
            states["intruded"] = 0

    def getIPTrafficState(self):
        ipstate = {}
        with self.stats_lock:
            for data in self.ip_stats:
                ip = data["ip"]
                traffic_group = data["traffic_group"]
                connection_type = data["connection_type"]

                key = "{}_{}".format(connection_type, traffic_group)

                if ip not in ipstate:
                    ipstate[ip] = {}
                if key not in ipstate[ip]:
                    ipstate[ip][key] = {"count": 0, "connection_type": connection_type, "blocklist_name": data["blocklist_name"], "traffic_group": data["traffic_group"], "last": 0}
                ipstate[ip][key]["count"] += 1
                if data["time"] > ipstate[ip][key]["last"]:
                    ipstate[ip][key]["last"] = data["time"]
        #logging.info("getIPTrafficState: {}".format(ipstate))
        return ipstate

    def getLastTrafficStatsTime(self, connection_type):
        with self.stats_lock:
            return self.last_traffic_stats[connection_type] if connection_type in self.last_traffic_stats else 0

    def getTrafficState(self):
        count_values = {}
        with self.stats_lock:
            for group in self.traffic_stats:
                count_values[group] = len(self.traffic_stats[group])
        self._fillTrafficStates(count_values)
        return count_values

    def getBlockedIPs(self):
        return self.trafficblocker.getBlockedIPs()

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

    def getMessurements(self):
        messurements = []

        wireguard_peers = None

        registry = {}
        for con in list(self.connections):
            self.connections.remove(con)

            if con.skipped:
                continue

            timestamp = con.timestamp

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

            base_tags = {}
            state_tags = {}
            values = {}

            src_is_external = con.src_is_external
            extern_ip = str((con.src if src_is_external else con.dest).compressed)
            extern_hostname = con.src_hostname if src_is_external else con.dest_hostname
            intern_ip = str((con.dest if src_is_external else con.src).compressed)
            intern_hostname = con.dest_hostname if src_is_external else con.src_hostname

            service = con.service

            if not self.trafficblocker.isApprovedIPs(extern_ip):
                blocklist_name = self.blocklists.check(extern_ip)
                if not blocklist_name and src_is_external and len(self.allowed_isp_pattern) > 0:
                    allowed = False
                    service_key = Helper.getServiceKey(con.dest, con.dest_port) if src_is_external else None
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

            if con.isFilteredTrafficGroup(traffic_group):
                #logging.info("{} {}".format(extern_ip, "filtered"))
                continue

            direction = "incoming" if src_is_external else "outgoing"

            is_blocked = self.trafficblocker.isBlockedIP(extern_ip)

            if traffic_group != "normal":
                with self.stats_lock:
                    self._addTrafficState(con.connection_type, extern_ip, traffic_group, blocklist_name, timestamp)

                messurements.append("trafficevents,connection_type={},extern_ip={},traffic_group={},blocklist_name={} value=1 {}".format(con.connection_type, extern_ip, traffic_group, blocklist_name, int(timestamp * 1000)))

                if not is_blocked:
                    data = {
                        "type": con.connection_type,
                        "time": str(datetime.fromtimestamp(timestamp)),
                        "extern_ip": extern_ip,
                        "intern_ip": intern_ip,
                        "direction": direction,
                        "traffic_group": traffic_group
                    }
                    con.applyDebugFields(data)
                    logging.info("SUSPICIOUS TRAFFIC: {}".format(data))

            base_tags["intern_ip"] = intern_ip
            base_tags["intern_host"] = intern_hostname

            base_tags["extern_ip"] = extern_ip
            base_tags["extern_host"] = extern_hostname
            extern_group = extern_hostname
            m = re.search('^.*?([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+|[a-z0-9-]+\.[a-z0-9]+)$', extern_group)
            if m and m.group(1) != extern_group:
                extern_group = "*.{}".format(m.group(1))
            base_tags["extern_group"] = extern_group

            base_tags["service"] = service

            base_tags["direction"] = direction
            base_tags["protocol"] = con.protocol_name

            base_tags["ip_type"] = con.ip_type

            base_tags["destination_port"] = con.dest_port

            base_tags["location_country_name"] = location_country_name
            base_tags["location_country_code"] = location_country_code
            base_tags["location_zip"] = location_zip
            base_tags["location_city"] = location_city
            if location_org:
                base_tags["location_org"] = location_org

            #base_tags["oneway={}".format(1 if con.is_one_direction else 0))

            #logging.info("SRC: {} {} {}".format(con.src, con.src_hostname,src_location))
            #logging.info("DEST: {} {} {}".format(con.dest, con.dest_hostname,dest_location))

            if location_geohash:
                values["location_geohash"] = location_geohash
                base_tags["location_has_geohash"] = 1

            values["blocked"] = 1 if is_blocked else 0

            base_tags_r = []
            for name, value in base_tags.items():
                base_tags_r.append(str(value))
            key = ",".join(base_tags_r)
            #logging.info(base_tags_str)

            #if traffic_group != "normal":
            #    logging.info("KEY: {}".format(key))

            data = None
            if key in registry:
                for _data in registry[key]:
                    if abs(_data["timestamp"] - timestamp) <= 1:
                        if traffic_group != "normal":
                            logging.info("FOUND REGISTRY {} {} {}".format(con.connection_type, str(datetime.fromtimestamp(timestamp)), extern_ip))
                        data = _data
                        break
            else:
                registry[key] = []
            if data is None:
                if key in self.last_registry:
                    for _data in self.last_registry[key]:
                        if abs(_data["timestamp"] - timestamp) <= 1:
                            if traffic_group != "normal":
                                logging.info("FOUND LAST REGISTRY {} {} {}".format(con.connection_type, str(datetime.fromtimestamp(timestamp)), extern_ip))
                            data = _data
                            break
                if data is None:
                    data = {"base_tags": base_tags, "state_tags": state_tags, "values": values, "timestamp": timestamp, "influxdb_timestamp": int(timestamp) * 1000, "query": None}
                registry[key].append(data)

            if "group" in data["state_tags"]:
                if TrafficGroup.PRIORITY[data["state_tags"]["group"]] < TrafficGroup.PRIORITY[traffic_group]:
                    data["state_tags"]["group"] = traffic_group
            else:
                data["state_tags"]["group"] = traffic_group

            con.applyData(data, traffic_group)

        self.last_registry = registry

        data_r = []
        for _data_r in registry.values():
            data_r += _data_r

        cleanup_messurements = []
        sorted_data_r = sorted(data_r, key=lambda x: ["influxdb_timestamp"])
        for data in sorted_data_r:
            tags = data["base_tags"] | data["state_tags"]

            tag_str_r = []
            for name, value in tags.items():
                if isinstance(value, str):
                    tag_str_r.append("{}={}".format(name,InfluxDB.escapeTagValue(value)))
                else:
                    tag_str_r.append("{}={}".format(name,value))
            tag_str = ",".join(tag_str_r)

            values_r = []
            for name,value in data["values"].items():
                if isinstance(value, list):
                    values_r.append("{}=\"{}\"".format(name,value[1](value[0])))
                elif isinstance(value, str):
                    values_r.append("{}=\"{}\"".format(name,InfluxDB.escapeFieldValue(value)))
                else:
                    values_r.append("{}={}".format(name,value))
            value_str = ",".join(values_r)

            if data["query"] is not None and data["query"][1] != tag_str:
                #logging.info("CLEANUP => OLD TAGS: {}".format(data["query"][1]))
                #logging.info("CLEANUP => NEW TAGS: {}".format(tag_str))
                cleanup_messurements.append(["trafficflow", data["query"][0], data["influxdb_timestamp"]])

            data["query"] = [ tags, tag_str ]
            messurements.append("trafficflow,{} {} {}".format(tag_str, value_str, data["influxdb_timestamp"]))


        #end = time.time()
        #logging.info("METRIC PROCESSING FINISHED in {} seconds".format(round(end-start,1)))
        #pr.disable()
        #if (end-start) > 0.5:
        #    s = io.StringIO()
        #    sortby = SortKey.CUMULATIVE
        #    ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
        #    ps.print_stats()
        #    logging.info(s.getvalue())

        counter_values = self.ipcache.getCountStats()
        logging.info("Cache statistic - LOCATION [fetch: {}, cache {}/{}], HOSTNAME [fetch: {}, cache {}/{}]".format(counter_values["location_fetch"], counter_values["location_cache"], self.ipcache.getLocationSize(), counter_values["hostname_fetch"], counter_values["hostname_cache"], self.ipcache.getHostnameSize()))

        self.trafficblocker.triggerCheck()

        if len(cleanup_messurements) > 0:
            start_cleanup = time.time()

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

            logging.info(queries)
            result = self.influxdb.delete(queries)

            end_cleanup = time.time()
            logging.info("CLEANUP => done after {} seconds".format(end_cleanup-start_cleanup))

        return messurements

    def getStateMetrics(self):
        metrics = ["system_service_process{{type=\"trafficwatcher\"}} {}".format("1" if self.is_running else "0")]

        min_time = self.last_processed_traffic_stats
        self.last_processed_traffic_stats = max(self.last_traffic_stats.values()) if len(self.last_traffic_stats) > 0 else 0

        count_values = {}
        with self.stats_lock:
            for group in list(self.traffic_stats.keys()):
                values = [time for time in self.traffic_stats[group] if time > min_time]
                count_values[group] = len(values)
            self._fillTrafficStates(count_values)

        for group, count in count_values.items():
            metrics.append( "system_service_trafficwatcher{{type=\"{}\",}} {}".format( group, count ) )

        metrics = metrics + self.logcollector.getStateMetrics()
        metrics = metrics + self.netflow.getStateMetrics()
        metrics = metrics + self.blocklists.getStateMetrics()
        metrics = metrics + self.trafficblocker.getStateMetrics()

        return metrics
