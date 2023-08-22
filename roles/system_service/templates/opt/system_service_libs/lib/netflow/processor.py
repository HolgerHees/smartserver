#import netflow # https://github.com/bitkeks/python-netflow-v9-softflowd
import queue
import threading
import logging
import traceback
import time
from datetime import datetime, timezone
import re
import schedule

import socket
import ipaddress
import contextlib

import cProfile, pstats, io
from pstats import SortKey

from .collector import ThreadedNetFlowListener

from lib.influxdb import InfluxDB
from lib.ipcache import IPCache

from smartserver import command


IP_PROTOCOLS = {
    1: "icmp",
    2: "igmp",
    6: "tcp",
    17: "udp",
    58: "icmpv6"
}

IP_PING_PROTOCOLS = [1,58]
IP_DATA_PROTOCOLS = [6,17]

TCP_FLAGS = {
    1: "FIN",  # Finish
    2: "SYN",  # Synchronization
    4: "RST",  # Reset
    8: "PSH",  # Push
    16: "ACK", # Acknowledge
    32: "URG", # Urgent
    64: "ECN", # Echo
    128: "CWR" # Congestion Window Reduced
}

#TCP_FLAG_TYPES = {
#    "ACK": 16
#}

# ICMP RFC
# - https://www.iana.org/assignments/icmp-parameters/icmp-parameters.xhtml
# NETFLOW SPEC
# - Internet Control Message Protocol (ICMP) packet type; reported as ((ICMP Type*256) + ICMP code)
# - https://www.cisco.com/en/US/technologies/tk648/tk362/technologies_white_paper09186a00800a3db9.html
ICMP_TYPES = {
    "ECHO_REPLY": 0 * 256,
    "ECHO_REQUEST": 8 * 256,
    "TIME_REPLY": 14 * 256,
    "EXTENDED_ECHO_REPLY": 43 * 256
}

#MDNS_IP4 = ipaddress.IPv4Address("224.0.0.251")
#SSDP_IP4 = ipaddress.IPv4Address("239.255.255.250")
#BROADCAST_IP4 = ipaddress.IPv4Address("255.255.255.255")

METRIC_TIMESHIFT = 60
PROMETHEUS_INTERVAL = 60

WIREGUARD_PEER_TIMEOUT = 60 * 5 # 5 minutes

class TrafficGroup():
    NORMAL = 'normal'
    OBSERVED = 'observed'
    SCANNING = 'scanning'
    INTRUDED = 'intruded'

class Helper():
    __base32 = '0123456789bcdefghjkmnpqrstuvwxyz'

    @staticmethod
    def getService(port, protocol):
        if protocol in IP_DATA_PROTOCOLS and port is not None and port < 1024:
            with contextlib.suppress(OSError):
                return socket.getservbyport(port, IP_PROTOCOLS[protocol])
        return None

    @staticmethod
    def getServiceKey(ip, port):
        return "{}:{}".format(ip.compressed, port)

    @staticmethod
    def fallback(d, keys, can_none = False ):
        for k in keys:
            if k in d:
                return d[k]
        if can_none:
            return None
        raise KeyError( "{} - {}".format(", ".join(keys), d.keys()))

    #@staticmethod
    #def isExpectedTraffic(service_key, config):
    #    if config.netflow_incoming_traffic and service_key in config.netflow_incoming_traffic:
    #        return True
    #    return False

    def checkFlag(flags, flag):
        if flag == 0:
            return flags == 0
        return flags & flag == flag

    @staticmethod
    def shouldSwapDirection(connection, config, cache):
        srcIsExternal = cache.isExternal(connection.src)

        if connection.protocol in IP_PING_PROTOCOLS:
            return srcIsExternal
            #if Helper.checkFlag(connection.request_icmp_flags, ICMP_TYPES["ECHO_REPLY"]): # is an answer flow
            #    return True
            #if Helper.checkFlag(connection.request_icmp_flags, ICMP_TYPES["TIME_REPLY"]): # is an answer flow
            #    return True
            #if Helper.checkFlag(connection.request_icmp_flags, ICMP_TYPES["EXTENDED_ECHO_REPLY"]): # is an answer flow
            #    return True
            #if Helper.checkFlag(connection.request_icmp_flags, ICMP_TYPES["ECHO_REQUEST"]): # can only happen from inside, because gateway firewall is blocking/nat traffic
            #    return True
        elif connection.protocol in IP_DATA_PROTOCOLS:
            #if connection.answer_tcp_flags is not None:
            #    if Helper.checkFlag(connection.request_tcp_flags, TCP_FLAG_TYPES["ACK"]): # is an answer flow
            #        return True
            if connection.src_port is not None and connection.dest_port is not None:
                if config.netflow_incoming_traffic:
                    if srcIsExternal:
                        if Helper.getServiceKey(connection.dest, connection.dest_port) not in config.netflow_incoming_traffic:
                            return True
                    else:
                        if Helper.getServiceKey(connection.src, connection.src_port) in config.netflow_incoming_traffic:
                            return True
                else:
                    if connection.src_port < 1024 and connection.dest_port >= 1024:
                        return True
            return False
        else:
            return srcIsExternal

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

class Connection:
    def __init__(self, request_ts, request_flow, answer_flow, config, cache):
        self.request_ts = request_ts
        self.request_flow = request_flow
        self.answer_flow = answer_flow

        self.config = config
        self.cache = cache

        self.protocol = self.request_flow["PROTOCOL"]

        if request_flow.get('IP_PROTOCOL_VERSION') == 4 or 'IPV4_SRC_ADDR' in request_flow or 'IPV4_DST_ADDR' in request_flow:
            self.src_raw = request_flow['IPV4_SRC_ADDR']
            self.src = ipaddress.ip_address(self.src_raw)
            self.dest_raw = request_flow['IPV4_DST_ADDR']
            self.dest = ipaddress.ip_address(self.dest_raw)
            self.ip_type = "v4"
        else:
            self.src_raw = request_flow['IPV6_SRC_ADDR']
            self.src = ipaddress.ip_address(self.src_raw)
            self.dest_raw = request_flow['IPV6_DST_ADDR']
            self.dest = ipaddress.ip_address(self.dest_raw)
            self.ip_type = "v6"

        self.src_port = self.request_flow['L4_SRC_PORT'] if 'L4_SRC_PORT' in self.request_flow else None
        self.dest_port = self.request_flow['L4_DST_PORT'] if 'L4_DST_PORT' in self.request_flow else None

        self.request_icmp_flags = self.request_flow['ICMP_TYPE'] if 'ICMP_TYPE' in self.request_flow else None
        self.request_tcp_flags = self.request_flow['TCP_FLAGS'] if 'TCP_FLAGS' in self.request_flow else None

        self.answer_icmp_flags = self.answer_flow['ICMP_TYPE'] if self.answer_flow is not None and 'ICMP_TYPE' in self.answer_flow else None
        self.answer_tcp_flags = self.answer_flow['TCP_FLAGS'] if self.answer_flow is not None and 'TCP_FLAGS' in self.answer_flow else None

        # swap direction
        if Helper.shouldSwapDirection(self, config, cache):
           #or not self.src.is_private:
            _ = self.dest_port
            self.dest_port = self.src_port
            self.src_port = _

            _ = self.dest
            self.dest = self.src
            self.src = _

            _ = self.dest_raw
            self.dest_raw = self.src_raw
            self.src_raw = _

            if self.answer_tcp_flags is not None:
                _ = self.request_tcp_flags
                self.request_tcp_flags = self.answer_tcp_flags
                self.answer_tcp_flags = _

            if self.answer_icmp_flags is not None:
                _ = self.request_icmp_flags
                self.request_icmp_flags = self.answer_icmp_flags
                self.answer_icmp_flags = _

            self.is_swapped = True
        else:
            self.is_swapped = False

        self.size = Helper.fallback(self.request_flow, ['IN_BYTES', 'IN_OCTETS']) + ( Helper.fallback(self.answer_flow, ['IN_BYTES', 'IN_OCTETS']) if self.answer_flow is not None else 0 )
        self.packages = self.request_flow["IN_PKTS"] + ( self.answer_flow["IN_PKTS"] if self.answer_flow is not None else 0 )

        # Duration is given in milliseconds
        self.duration = self.request_flow['LAST_SWITCHED'] - self.request_flow['FIRST_SWITCHED']
        if self.duration < 0:
            # 32 bit int has its limits. Handling overflow here
            # TODO: Should be handled in the collection phase
            self.duration = (2 ** 32 - self.request_flow['FIRST_SWITCHED']) + self.request_flow['LAST_SWITCHED']

        self.is_multicast = True if self.dest.is_multicast or self.src.is_multicast else False
        self.is_broadcast = True if self.dest.compressed.endswith(".255") or self.src.compressed.endswith(".255") else False
        self.skipped = self.is_multicast or self.is_broadcast

        if not self.skipped:
            self._location = self.cache.getLocation(self.src if self.src.is_global else self.dest, True)

            self._src_hostname = self.cache.getHostname(self.src, True)
            self._dest_hostname = self.cache.getHostname(self.dest, True)

        #if self.src.is_global and self.dest_port not in [80,10114,51828,51829]:
        #    logging.error("WIRED")
        #    logging.error(self.request_flow)
        #    logging.error(self.is_swapped)
        #elif self.is_swapped:
        #    logging.info("SWAPPED {} => {}".format(self.src,self.dest))


#Apr 03 15:10:49 marvin system_service[3445]: [INFO] - [lib.netflow.processor:121] - {'IPV4_SRC_ADDR': '34.158.0.131', 'IPV4_DST_ADDR': '192.168.0.108', 'FIRST_SWITCHED': 24968747, 'LAST_SWITCHED': 25030465, 'IN_BYTES': 441, 'IN_PKTS': 7, 'INPUT_SNMP': 0, 'OUTPUT_SNMP': 0, 'L4_SRC_PORT': 4070, 'L4_DST_PORT': 48096, 'PROTOCOL': 6, 'TCP_FLAGS': 24, 'IP_PROTOCOL_VERSION': 4, 'SRC_TOS': 0}
#Apr 03 15:10:49 marvin system_service[3445]: [INFO] - [lib.netflow.processor:122] - False

        #logging.info(self.duration)
    def getRequestFlow(self):
        return self.request_flow

    def getAnswerFlow(self):
        return self.answer_flow

    @property
    def protocol_name(self):
        return IP_PROTOCOLS[self.protocol]

    @property
    def is_one_direction(self):
        return self.answer_flow is None

    @property
    def service(self):
        if self.is_multicast:
            service = "multicast"
        elif self.protocol in IP_PING_PROTOCOLS:
            if Helper.checkFlag(self.request_icmp_flags, ICMP_TYPES["ECHO_REQUEST"]):
                service = "ping"
            else:
                service = "icmp"
        else:
            service = Helper.getService(self.dest_port, self.protocol)
            if service is None:
                service_key = Helper.getServiceKey(self.dest, self.dest_port)
                if service_key in self.config.netflow_incoming_traffic:
                    service = self.config.netflow_incoming_traffic[service_key]["name"].replace(" ","\\ ").replace(",","\\,")
                elif "speedtest" in self.dest_hostname:
                    service = "speedtest"
                else:
                    service = "unknown"
        return service

    @property
    def src_hostname(self):
        return self._src_hostname if self._src_hostname is not None else self.cache.getHostname(self.src, False)

    @property
    def dest_hostname(self):
        return self._dest_hostname if self._dest_hostname is not None else self.cache.getHostname(self.dest, False)

    @property
    def location(self):
        return self._location if self._location is not None else self.cache.getLocation(self.src if self.src.is_global else self.dest, False)

class Processor(threading.Thread):
    def __init__(self, config, handler, influxdb, ipcache, malware ):
        threading.Thread.__init__(self)

        self.is_running = False

        self.config = config

        self.is_enabled = True

        self.ip_stats = []
        self.traffic_stats = {}
        self.last_traffic_stats = 0
        self.last_processed_traffic_stats = 0
        self.stats_lock = threading.Lock()

        self.connections = []
        self.last_registry = {}
        #self.last_metric_end = time.time() - METRIC_TIMESHIFT
        #self.suspicious_ips = {}

        self.cache = ipcache

        self.malware = malware
        self.handler = handler

        self.influxdb = influxdb

        self.wireguard_peers = {}
        self.allowed_isp_pattern = {}
        for target, data in config.netflow_incoming_traffic.items():
            self.allowed_isp_pattern[target] = {}
            for field, pattern in data["allowed"].items():
                self.allowed_isp_pattern[target][field] = re.compile(pattern, re.IGNORECASE)

    def terminate(self):
        self.is_running = False

    def start(self):
        self.is_running = True

        schedule.every().minute.at(":00").do(self._cleanTrafficState)
        self.influxdb.register(self.getMessurements)

        super().start()

    def run(self):
        if self.config.netflow_bind_ip is None:
            return

        logging.info("Init traffic state")
        while True:
            try:
                self._initTrafficState()
                break
            except Exception as e:
                logging.info(e)
                logging.info("InfluxDB not ready. Will retry in 15 seconds.")
                time.sleep(15)

        logging.info("Netflow processor started")

        #collectorLogger.setLevel(logging.DEBUG)
        #collectorCS.setLevel(logging.DEBUG)

        self.listener = ThreadedNetFlowListener(self.config.netflow_bind_ip, self.config.netflow_bind_port)
        self.listener.start()

        try:
            pending = {}
            last_cleanup = datetime.now().timestamp()

            while self.is_running:
                try:
                    ts, client, export = self.listener.get(timeout=0.5)

                    #flows = []
                    #for f in export.flows:
                    #    flows.append(f.data)

                    if not self.is_enabled:
                        #logging.info("Netflow flows: {}".format(len(flows)))
                        continue

                    if export.header.version != 9:
                        logging.error("Unsupported netflow version {}. Only version 9 is supported.".format(export.header.version))
                        continue

                    #for flow in sorted(flows, key=lambda x: x["FIRST_SWITCHED"]):
                    for f in export.flows:
                        flow = f.data

                        #logging.info(flow)

                        if "PROTOCOL" not in flow:
                            if "ICMP_TYPE" in flow:
                                flow["PROTOCOL"] = 1
                            elif "MUL_IGMP_TYPE" in flow:
                                flow["PROTOCOL"] = 2
                            else:
                                flow["PROTOCOL"] = 0

                        if flow["PROTOCOL"] not in IP_PROTOCOLS:
                            flow["PROTOCOL"] = 17
                            #logging.info("Unknown protocol {}".format(flow["PROTOCOL"]))
                            #logging.info(flow)
                            #continue

                        first_switched = flow["FIRST_SWITCHED"]

                        #if first_switched - 1 in pending:
                        #    # TODO: handle fitting, yet mismatching (here: 1 second) pairs
                        #    pass

                        # Find the peer for this connection
                        if "IPV4_SRC_ADDR" in flow or flow.get("IP_PROTOCOL_VERSION") == 4:
                            src_addr = flow["IPV4_SRC_ADDR"]
                            dest_addr = flow["IPV4_DST_ADDR"]
                        else:
                            src_addr = flow["IPV6_SRC_ADDR"]
                            dest_addr = flow["IPV6_DST_ADDR"]

                        #if src_addr == client[0] or dest_addr == client[0]:
                        #    logging.info("SKIPPED")
                        #    logging.info(flow)
                        #    continue

                        #if first_switched not in pending:
                        #    pending[first_switched] = {}

                        # Match peers
                        _request_key = "{}-{}".format(dest_addr,first_switched)
                        if _request_key in pending:
                            request_flow, request_ts = pending.pop(_request_key)
                            answer_flow = flow
                        else:
                            _request_key = "{}-{}".format(dest_addr,first_switched - 1)
                            if _request_key in pending:
                                request_flow, request_ts = pending.pop(_request_key)
                                answer_flow = flow
                            else:
                                request_key = "{}-{}".format(src_addr,first_switched)
                                if request_key in pending:
                                    request_flow, request_ts = pending.pop(request_key)
                                    con = Connection(request_ts, request_flow, None, self.config, self.cache)
                                    self.connections.append(con)
                                pending[request_key] = [ flow, ts ]
                                continue

                        #logging.info("{}".format(peer_flow))
                        #logging.info("{}".format(flow))
                        #logging.info("---------")

                        #raise Exception

                        con = Connection(request_ts, request_flow, answer_flow, self.config, self.cache)
                        self.connections.append(con)

                    #self.getMetrics()

                except queue.Empty:
                    pass
                except Exception:
                    logging.error(traceback.format_exc())

                now = datetime.now().timestamp()
                if now - last_cleanup >= 1:
                    for request_key in list(pending.keys()):
                        request_flow, request_ts = pending[request_key]
                        if ts - request_ts > 15:
                            con = Connection(request_ts, request_flow, None, self.config, self.cache)
                            self.connections.append(con)
                            del pending[request_key]
                    last_cleanup = now

            logging.info("Netflow processor stopped")
        except Exception:
            logging.error(traceback.format_exc())
            self.is_running = False
        finally:
            self.listener.stop()
            self.listener.join()

    def getWireguardPeers(self):
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
        # ******
        #start = time.time()
        #pr = cProfile.Profile()
        #pr.enable()

        wireguard_peers = None
        approved_ips = self.handler.getTrafficBlocker().getApprovedIPs()
        blocked_ips = self.handler.getTrafficBlocker().getBlockedIPs()

        registry = {}
        for con in list(self.connections):
            self.connections.remove(con)

            if con.skipped:
                continue

            timestamp = con.request_ts

            # most flows are already 60 seconds old when they are delivered (flow expire config in softflowd)
            timestamp -= METRIC_TIMESHIFT
            influx_timestamp = int(int(timestamp) * 1000)

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

            label = []
            values = {}

            _srcIsExternal = self.cache.isExternal(con.src)
            extern_ip = str((con.src if _srcIsExternal else con.dest).compressed)
            extern_hostname = con.src_hostname if _srcIsExternal else con.dest_hostname
            intern_ip = str((con.dest if _srcIsExternal else con.src).compressed)
            intern_hostname = con.dest_hostname if _srcIsExternal else con.src_hostname

            label.append("intern_ip={}".format(intern_ip))
            label.append("intern_host={}".format(intern_hostname))

            label.append("extern_ip={}".format(extern_ip))
            label.append("extern_host={}".format(extern_hostname))
            extern_group = extern_hostname
            m = re.search('^.*?([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+|[a-z0-9-]+\.[a-z0-9]+)$', extern_group)
            if m and m.group(1) != extern_group:
                extern_group = "*.{}".format(m.group(1))
            #for provider in ["amazonaws.com","awsglobalaccelerator.com","cloudfront.net","akamaitechnologies.com","googleusercontent.com"]:
            #    if provider in extern_hostname:
            #        extern_group = "*.{}".format(provider)
            #        break
            label.append("extern_group={}".format(extern_group))

            service = con.service
            label.append("service={}".format(service))

            traffic_group = TrafficGroup.NORMAL
            if extern_ip not in approved_ips:
                malware_type = self.malware.check(extern_ip)
                if malware_type:
                    if _srcIsExternal:
                        traffic_group = TrafficGroup.SCANNING
                    else:
                        traffic_group = TrafficGroup.OBSERVED if service == "icmp" else TrafficGroup.INTRUDED
                elif _srcIsExternal and len(self.allowed_isp_pattern) > 0:
                    allowed = False
                    service_key = Helper.getServiceKey(con.dest, con.dest_port) if _srcIsExternal else None
                    if service_key in self.allowed_isp_pattern:
                        if location_org and "org" in self.allowed_isp_pattern[service_key] and self.allowed_isp_pattern[service_key]["org"].match(location_org):
                            allowed = True
                        elif extern_hostname and "hostname" in self.allowed_isp_pattern[service_key] and self.allowed_isp_pattern[service_key]["hostname"].match(extern_hostname):
                            allowed = True
                        elif extern_ip:
                            if "ip" in self.allowed_isp_pattern[service_key] and self.allowed_isp_pattern[service_key]["ip"].match(extern_ip):
                                allowed = True
                            elif "wireguard_peers" in self.allowed_isp_pattern[service_key] and ( wireguard_peers is not None or ( wireguard_peers := self.getWireguardPeers() ) ) and extern_ip in wireguard_peers:
                                allowed = True
                                #logging.info("wireguard >>>>>>>>>>> {}".format(extern_ip))
                    if not allowed:
                        traffic_group = TrafficGroup.OBSERVED
                        malware_type = "unknown"
            else:
                malware_type = None
            label.append("group={}".format(traffic_group))

            direction = "incoming" if _srcIsExternal else "outgoing"
            label.append("direction={}".format(direction))
            label.append("protocol={}".format(con.protocol_name))

            label.append("ip_type={}".format(con.ip_type))

            label.append("destination_port={}".format(con.dest_port))
            #label.append("source_port={}".format(con.src_port)) # => should be a field, because it is changing every time
            #label.append("size={}".format(con.size))
            #label.append("duration={}".format(con.duration))
            #label.append("packets={}".format(con.packages))

            label.append("location_country_name={}".format(InfluxDB.escapeValue(location_country_name)))
            label.append("location_country_code={}".format(location_country_code))
            label.append("location_zip={}".format(InfluxDB.escapeValue(location_zip)))
            label.append("location_city={}".format(InfluxDB.escapeValue(location_city)))
            if location_org:
                label.append("location_org={}".format(InfluxDB.escapeValue(location_org)))

            #label.append("oneway={}".format(1 if con.is_one_direction else 0))

            #logging.info("SRC: {} {} {}".format(con.src, con.src_hostname,src_location))
            #logging.info("DEST: {} {} {}".format(con.dest, con.dest_hostname,dest_location))

            if location_geohash:
                values["location_geohash"] = location_geohash
                label.append("location_geohash=1")

            values["tcp_flags"] = con.request_tcp_flags if con.request_tcp_flags is not None else 0
            values["size"] = con.size
            values["count"] = 1

            label_str = ",".join(label)
            key = "{}-{}".format(label_str, influx_timestamp)
            if key not in registry:
                #logging.info("new")
                registry[key] = [label_str, values, influx_timestamp]

                #logging.info("timestamp: {}, influx_timestamp: {}".format(timestamp, influx_timestamp))

                # old values with same timestamp should be summerized
                if key in self.last_registry:
                    registry[key][1]["tcp_flags"] |= self.last_registry[key][1]["tcp_flags"]
                    registry[key][1]["size"] += self.last_registry[key][1]["size"]
                    registry[key][1]["count"] += self.last_registry[key][1]["count"]
            else:
                registry[key][1]["tcp_flags"] |= values["tcp_flags"]
                registry[key][1]["size"] += values["size"]
                registry[key][1]["count"] += 1

            #logging.info("INIT {}".format(datetime.fromtimestamp(timestamp)))
            #logging.info("{} {}".format(timestamp, influx_timestamp))
            if traffic_group != "normal":
                with self.stats_lock:
                    self._addTrafficState(extern_ip, traffic_group, malware_type, timestamp)

                if extern_ip not in blocked_ips:
                    #if traffic_group == "intruded":
                    data = {
                        "extern_ip": extern_ip,
                        "intern_ip": intern_ip,
                        "direction": direction,
                        "type": traffic_group,
                        "request": con.getRequestFlow(),
                        "response": con.getAnswerFlow()
                    }
                    logging.info("SUSPICIOUS TRAFFIC: {}".format(data))

            #if con.protocol in IP_PING_PROTOCOLS:
            #    data = {
            #        "extern_ip": str(extern_ip),
            #        "intern_ip": str(intern_ip),
            #        "direction": direction,
            #        "type": traffic_group,
            #        "request": con.getRequestFlow(),
            #        "response": con.getAnswerFlow()
            #    }
            #    logging.info(data)

        self.last_registry = registry

        messurements = []
        sorted_registry = sorted(registry.values(), key=lambda x: x[2])
        for data in sorted_registry:

            label_str, values, timestamp = data

            flags = []
            if values["tcp_flags"] > 0:
                for flag, name in TCP_FLAGS.items():
                    if flag & values["tcp_flags"] == flag:
                        flags.append(name)
            if len(flags) == 0:
                flags.append("NONE")

            values_str = []
            values_str.append("tcp_flags=\"{}\"".format("|".join(flags)))
            for name,value in values.items():
                if name == "tcp_flags":
                    continue
                elif isinstance(value, str):
                    values_str.append("{}=\"{}\"".format(name,InfluxDB.escapeValue(value)))
                else:
                    values_str.append("{}={}".format(name,value))
            values_str = ",".join(values_str)

            #logging.info("netflow,{} {} {}".format(label_str, values_str, timestamp))

            messurements.append("netflow,{} {} {}".format(label_str, values_str, timestamp))

        #end = time.time()
        #logging.info("METRIC PROCESSING FINISHED in {} seconds".format(round(end-start,1)))
        #pr.disable()
        #if (end-start) > 0.5:
        #    s = io.StringIO()
        #    sortby = SortKey.CUMULATIVE
        #    ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
        #    ps.print_stats()
        #    logging.info(s.getvalue())

        counter_values = self.cache.getCountStats()
        logging.info("Cache statistic - LOCATION [fetch: {}, cache {}/{}], HOSTNAME [fetch: {}, cache {}/{}]".format(counter_values["location_fetch"], counter_values["location_cache"], self.cache.getLocationSize(), counter_values["hostname_fetch"], counter_values["hostname_cache"], self.cache.getHostnameSize()))

        #logging.info(messurements)

        #self.last_metric_end = time.time() - METRIC_TIMESHIFT

        return messurements

    def _cleanTrafficState(self):
        with self.stats_lock:
            min_time = datetime.now().timestamp() - 60 * 60 * 6

            for group in list(self.traffic_stats.keys()):
                values = [time for time in self.traffic_stats[group] if time > min_time]
                if len(values) == 0:
                    del self.traffic_stats[group]
                else:
                    self.traffic_stats[group] = values

            self.ip_stats = [data for data in self.ip_stats if data["time"] > min_time]

    def _initTrafficState(self):
        with self.stats_lock:
            # 362 min => 6h - 2 min
            results = self.influxdb.query('SELECT "extern_ip","group","count" FROM "netflow" WHERE time >= now() - 358m AND "group"::tag != \'normal\'')
            self.traffic_stats = {}
            if results is not None:
                for result in results:
                    for value in result["values"]:
                        #if value[3] > 1:
                        #    logging.info("{} {} {}".format(value[1], value[2], value[3]))
                        value_time = InfluxDB.parseDatetime(value[0])
                        malware_type = self.malware.check(value[1])
                        for n in range(value[3]):
                            self._addTrafficState(value[1], value[2], malware_type if malware_type else "unknown", value_time.timestamp())
            self.last_processed_traffic_stats = self.last_traffic_stats

    def _addTrafficState(self, ip, traffic_group, malware_type, time):
        # lock is called in place where this function is called

        #logging.info("ADD {}".format(datetime.fromtimestamp(time)))
        if traffic_group not in self.traffic_stats:
            self.traffic_stats[traffic_group] = []
        self.traffic_stats[traffic_group].append(time)
        if time > self.last_traffic_stats:
            self.last_traffic_stats = time

        self.ip_stats.append({"ip": ip, "traffic_group": traffic_group, "malware_type": malware_type, "time": time})

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

                key = "netflow_{}".format(traffic_group)

                if ip not in ipstate:
                    ipstate[ip] = {}
                if key not in ipstate[ip]:
                    ipstate[ip][key] = {"count": 0, "reason": "netflow", "type": data["malware_type"], "details": data["traffic_group"], "last": 0}
                ipstate[ip][key]["count"] += 1
                if data["time"] > ipstate[ip][key]["last"]:
                    ipstate[ip][key]["last"] = data["time"]

        return ipstate

    def getTrafficState(self):
        count_values = {}
        with self.stats_lock:
            for group in self.traffic_stats:
                count_values[group] = len(self.traffic_stats[group])
        self._fillTrafficStates(count_values)
        return count_values

    def getStateMetrics(self):
        metrics = [ "system_service_process{{type=\"netflow_processor\",}} {}".format("1" if self.is_running else "0") ]

        min_time = self.last_processed_traffic_stats
        self.last_processed_traffic_stats = self.last_traffic_stats
        count_values = {}
        with self.stats_lock:
            for group in list(self.traffic_stats.keys()):
                values = [time for time in self.traffic_stats[group] if time > min_time]
                count_values[group] = len(values)
            self._fillTrafficStates(count_values)

        for group, count in count_values.items():
            metrics.append( "system_service_netflow{{type=\"{}\",}} {}".format( group, count ) )

        return metrics
