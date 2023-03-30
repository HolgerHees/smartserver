#import netflow # https://github.com/bitkeks/python-netflow-v9-softflowd
import queue
import threading
import logging
import traceback
import functools
import socket
import ipaddress
import contextlib
import time
from datetime import datetime

import requests
import json

import schedule
import os

from .collector import ThreadedNetFlowListener

IP_PROTOCOLS = {
    1: "icmp",
    2: "igmp",
    6: "tcp",
    17: "udp",
    58: "icmpv6"
}

MDNS_IP4 = ipaddress.IPv4Address("224.0.0.251")
SSDP_IP4 = ipaddress.IPv4Address("239.255.255.250")
BROADCAST_IP4 = ipaddress.IPv4Address("255.255.255.255")

METRIC_TIMESHIFT = 60
PROMETHEUS_INTERVAL = 60

class Helper():
    @staticmethod
    @functools.lru_cache(maxsize=None)
    def resolve_hostname(ip: str, is_private) -> str:
        hostname = socket.getfqdn(ip)
        if is_private and hostname != ip:
            hostname = hostname.split('.', 1)[0]
        return hostname

    @staticmethod
    def get_service(dest_port, protocol):
        if ( protocol == 6 or protocol == 17 ) and dest_port is not None and dest_port < 1024:
            with contextlib.suppress(OSError):
                return socket.getservbyport(dest_port, IP_PROTOCOLS[protocol])
        return None

    #@staticmethod
    #def human_size(size_bytes):
    #    # Calculate a human readable size of the flow
    #    if size_bytes < 1024:
    #        return "%dB" % size_bytes
    #    elif size_bytes / 1024. < 1024:
    #        return "%.2fK" % (size_bytes / 1024.)
    #    elif size_bytes / 1024. ** 2 < 1024:
    #        return "%.2fM" % (size_bytes / 1024. ** 2)
    #    else:
    #        return "%.2fG" % (size_bytes / 1024. ** 3)


    #@staticmethod
    #def human_duration(seconds):
    #    # Calculate human readable duration times
    #    if seconds < 60:
    #        # seconds
    #        return "%d sec" % seconds
    #    if seconds / 60 > 60:
    #        # hours
    #        return "%d:%02d.%02d hours" % (seconds / 60 ** 2, seconds % 60 ** 2 / 60, seconds % 60)
    #    # minutes
    #    return "%02d:%02d min" % (seconds / 60, seconds % 60)

    @staticmethod
    def fallback(d, keys, can_none = False ):
        for k in keys:
            if k in d:
                return d[k]
        if can_none:
            return None
        raise KeyError( "{} - {}".format(", ".join(keys), d.keys()))

class Connection:
    def __init__(self, request_ts, request_flow, answer_flow, config):
        self.request_ts = request_ts
        self.request_flow = request_flow
        self.answer_flow = answer_flow

        self.config = config

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

        # swap direction
        if ( \
             self.src_port is not None and self.dest_port is not None \
             and \
             ( \
               ( self.src_port < 1024 and self.dest_port >= 1024 ) \
                 or \
               ( self.src_port < 49151 and self.dest_port >= 49151 ) \
             ) \
           ) \
           or not self.src.is_private:
            _ = self.dest_port
            self.dest_port = self.src_port
            self.src_port = _
            _ = self.dest
            self.dest = self.src
            self.src = _
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

        #logging.info(self.duration)

    #@property
    #def human_size(self):
    #    return Helper.human_size(self.size)

    #@property
    #def human_duration(self):
    #    duration = self.duration // 1000  # uptime in milliseconds, floor it
    #    return Helper.human_duration(duration)

    @property
    def protocol_name(self):
        return IP_PROTOCOLS[self.protocol]

    @property
    def is_one_direction(self):
        return self.answer_flow is None

    @property
    def src_hostname(self):
        return Helper.resolve_hostname(self.src.compressed, self.src.is_private)

    @property
    def dest_hostname(self):
        return Helper.resolve_hostname(self.dest.compressed, self.dest.is_private)

    @property
    def service(self):
        service = Helper.get_service(self.dest_port, self.protocol)
        #logging.info("{} {} {}".format(service, self.dest_port, self.protocol))
        if service is None:
            if self.dest == MDNS_IP4 or self.dest_raw == "ff02:fb":
                service = "mdns"
            elif self.dest == SSDP_IP4 or self.dest_raw == "ff02:fb":
                service = "ssdp"
            elif self.dest == BROADCAST_IP4:
                service = "broadcast"
            elif self.dest.is_multicast:
                service = "multicast"
            else:
                known_service_key = "{}/{}".format(self.dest_port, IP_PROTOCOLS[self.protocol])
                if known_service_key in self.config.known_services:
                    return self.config.known_services[known_service_key]
                service = "unknown"
        return service

class Processor(threading.Thread):
    def __init__(self, config, handler, influxdb ):
        threading.Thread.__init__(self)

        self.is_running = True

        self.config = config

        self.is_enabled = True

        self.connections = []
        self.last_registry = {}
        #self.last_metric_end = time.time() - METRIC_TIMESHIFT

        influxdb.register(self.getMessurements)

        self.ip2location_state = True
        self.ip2location_map = {}

        #print(self.resolveLocation(ipaddress.ip_address("185.89.37.91")))
        #print(self.resolveLocation(ipaddress.ip_address("40.77.167.196")))
        #print(self.resolveLocation(ipaddress.ip_address("80.158.67.40")))
        #print(self.resolveLocation(ipaddress.ip_address("192.168.0.50")))
        #print(self.resolveLocation(ipaddress.ip_address("ff02::1:ff6d:914d")))
        #print(self.resolveLocation(ipaddress.ip_address("239.255.255.250")))

        #schedule.every().hour.at("00:00").do(self.fetchDatabase)

        #netflow_ip2location_url = "https://api.hostip.info/get_json.php?ip="
        #https://db-ip.com/db/download/ip-to-country-lite

        #https://github.com/sapics/ip-location-db

        # => http://www.iwik.org/ipcountry/

        self.ip2location_state = True
        self.ip2location_map = {}
        self.ip2location_db = "/tmp/ip2location.bin"
        #self.ip2location_database = IP2Location.IP2Location(os.path.join("tmp", "ip2location.db1.bin")) if os.path.exists(self.ip2location_db) else None

        self.fetchDatabase()

    #def fetchIpCountry(self, ip):
    #    self.ip2location_database

    def fetchDatabase(self):
        if os.path.exists(self.ip2location_db):
            st=os.stat(self.ip2location_db)
            age = time.time() - st.st_mtime
        else:
            age = time.time()

        if age > 60 * 60 * 24:
            pass
            #content = requests.get(self.config.ip2location_url)
            #zf = ZipFile(BytesIO(content.content))

            #for item in zf.namelist():
            #    if not item.endswith(".BIN"):
            #        continue

            #    tmp_file = "{}.tmp".format(self.ip2location_db)
            #    with zf.open(item) as f:
            #        with open(tmp_file, "wb") as _f:
            #            _f.write(f.read())

            #    if os.path.exists(tmp_file):
            #        st=os.stat(tmp_file)
            #        if st.st_size > 0:
            #            age = time.time() - st.st_mtime
            #            os.replace(tmp_file, self.ip2location_db)
            #            self.ip2location_database = IP2Location.IP2Location(os.path.join("tmp", "ip2location.db1.bin"))
            #            self.ip2location_map = {}
            #        else:
            #            os.remove(tmp_file)
            #    break


        self.ip2location_state = 1 if age < 60 * 60 * 24 * 2 else -1

        #self.ip2location_database.get_country_long("192.168.0.1")

    #def resolveLocation(self, ip):
    #    _ip = str(ip)
    #    location = self.ip2location_map.get(_ip, None)
    #    if location and time.time() - location["time"] > 60 * 60 * 24:
    #        location is None

    #    if location is None:
    #        if ip.is_private:
    #            location = { "data": { "country_name": "Private", "country_code": "xx", "city": "Private" }, "time": time.time() }
    #            self.ip2location_map[_ip] = None
    #        else:
    #            response = requests.get("{}{}".format(self.config.netflow_ip2location_url, _ip))

    #            if response.status_code == 200:
    #                try:
    #                    if len(response.content) > 0:
    #                        data = json.loads(response.content)
    #                        if "Private" in data["country_name"]:
    #                            location = { "data": {"country_name": "Private", "country_code": "xx", "city": "Private" }, "time": time.time() }
    #                        else:
    #                            if "Unknown" in data["country_name"]:
    #                                data["country_name"] = "Unknown"
    #                                data["country_code"] = "xx"
    #                                data["city"] = "Unknown"
    #                            location = { "data": {"country_name": data["country_name"].title().replace(" ","\\ ").replace(",","\\,"), "country_code": data["country_code"].lower(), "city": data["city"].replace(" ","\\ ").replace(",","\\,") }, "time": time.time() }
    #                    else:
    #                        location = { "data": { "country_name": "Unknown", "country_code": "xx", "city": "Unknown" }, "time": time.time() }
    #                    self.ip2location_map[_ip] = location
    #                    self.ip2location_state = True
    #                except:
    #                    logging.error("Error fetching ip {}".format(_ip))
    #                    logging.error(":{}:".format(response.content))
    #                    logging.error(traceback.format_exc())
    #                    return None
    #            else:
    #                self.ip2location_state = False
    #                return None

    #    return location["data"]

    def terminate(self):
        self.is_running = False

    def run(self):
        if self.config.netflow_bind_ip is None:
            return

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
                                    con = Connection(request_ts, request_flow, None, self.config)
                                    self.connections.append(con)
                                pending[request_key] = [ flow, ts ]
                                continue

                        #logging.info("{}".format(peer_flow))
                        #logging.info("{}".format(flow))
                        #logging.info("---------")

                        #raise Exception

                        con = Connection(request_ts, request_flow, answer_flow, self.config)
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
                            con = Connection(request_ts, request_flow, None, self.config)
                            self.connections.append(con)
                            del pending[request_key]
                    last_cleanup = now
        except Exception:
            logging.error(traceback.format_exc())
            self.is_running = False
        finally:
            self.listener.stop()
            self.listener.join()

    def getMessurements(self):
        messurements = []

        #f = open("/tmp/netflow.log", "w")
        #now = datetime.now().timestamp()

        start = time.time()
        logging.info("PROCESSING")

        registry = {}
        for con in list(self.connections):
            timestamp = con.request_ts

            # most flows are already 60 seconds old when they are delivered (flow expire config in softflowd)
            timestamp -= METRIC_TIMESHIFT

            #if timestamp < self.last_metric_end:
            #    #logging.info("fix {} by {}".format(con.answer_flow is not None, int(self.last_metric_end + 1) - timestamp))
            #    timestamp = int(self.last_metric_end + 1)

            src_location = None#self.resolveLocation(con.src)
            dest_location = None#self.resolveLocation(con.dest)

            label = []
            label.append("protocol={}".format(con.protocol_name))
            label.append("service={}".format(con.service))
            label.append("port={}".format(con.dest_port))
            #label.append("size={}".format(con.size))
            #label.append("duration={}".format(con.duration))
            #label.append("packets={}".format(con.packages))
            label.append("src_ip={}".format(con.src))
            label.append("src_host={}".format(con.src_hostname))
            if src_location is not None:
                label.append("src_country_name={}".format(src_location["country_name"]))
                label.append("src_country_code={}".format(src_location["country_code"]))
                label.append("src_city=\"{}\"".format(src_location["city"]))
            label.append("dest_ip={}".format(con.dest))
            label.append("dest_host={}".format(con.dest_hostname))
            if dest_location is not None:
                label.append("dest_country_name={}".format(dest_location["country_name"]))
                label.append("dest_country_code={}".format(dest_location["country_code"]))
                label.append("dest_city=\"{}\"".format(dest_location["city"]))
            label.append("ip_type={}".format(con.ip_type))
            #label.append("oneway={}".format(1 if con.is_one_direction else 0))

            label_str = ",".join(label)
            timestamp = int(timestamp * 1000)

            key = "{}-{}".format(label_str, timestamp)
            if key not in registry:
                #logging.info("new")
                registry[key] = [label_str, 0, timestamp]
            #else:
            #    logging.info("doublicate")

            registry[key][1] += con.size

            self.connections.remove(con)

        # old values with same timestamp should be summerized
        for _key in self.last_registry:
            if _key in registry:
                registry[_key][1] += self.last_registry[_key][1]
                #logging.info("last value")

        self.last_registry = registry

        messurements = []
        sorted_registry = sorted(registry.values(), key=lambda x: x[2])
        for data in sorted_registry:
            messurements.append("netflow_size,{} value={} {}".format(data[0], data[1], data[2]))

        end = time.time()

        logging.info("FINISHED in {} seconds".format(end-start))
        #logging.info(messurements)

        #logging.info(messurements)

        #self.last_metric_end = time.time() - METRIC_TIMESHIFT

        return messurements

    def getStateMetrics(self):
        return [
            "system_service_process{{type=\"netflow\",}} {}".format("1" if self.is_running else "0"),
            "system_service_process{{type=\"ip2location\",}} {}".format("1" if self.ip2location_state else "0"),
        ]
