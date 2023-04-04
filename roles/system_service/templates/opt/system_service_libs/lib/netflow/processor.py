#import netflow # https://github.com/bitkeks/python-netflow-v9-softflowd
import queue
import threading
import logging
import traceback
#import ipaddress
import time
from datetime import datetime

import socket
import ipaddress
import contextlib

import cProfile, pstats, io
from pstats import SortKey

from .collector import ThreadedNetFlowListener
from .cache import Cache

IP_PROTOCOLS = {
    1: "icmp",
    2: "igmp",
    6: "tcp",
    17: "udp",
    58: "icmpv6"
}

PING_PROTOCOLS = [1,58]

#MDNS_IP4 = ipaddress.IPv4Address("224.0.0.251")
#SSDP_IP4 = ipaddress.IPv4Address("239.255.255.250")
#BROADCAST_IP4 = ipaddress.IPv4Address("255.255.255.255")

METRIC_TIMESHIFT = 60
PROMETHEUS_INTERVAL = 60

class Helper():
    @staticmethod
    def getService(dest_port, protocol):
        if ( protocol == 6 or protocol == 17 ) and dest_port is not None and dest_port < 1024:
            with contextlib.suppress(OSError):
                return socket.getservbyport(dest_port, IP_PROTOCOLS[protocol])
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

    @staticmethod
    def shouldSwapDirection(connection, config):
        if config.netflow_incoming_traffic:
            return connection.src.is_global and Helper.getServiceKey(connection.dest, connection.dest_port) not in config.netflow_incoming_traffic

        return ( connection.protocol in PING_PROTOCOLS and connection.src.is_global ) \
               or \
               ( \
                   connection.src_port is not None and connection.dest_port is not None \
                   and \
                   ( \
                       ( connection.src_port < 1024 and connection.dest_port >= 1024 ) \
                       or \
                       ( connection.src_port < 9999 and connection.dest_port >= 9999 ) \
                       or \
                       ( connection.src_port < 49151 and connection.dest_port >= 49151 ) \
                   ) \
               )


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

        # swap direction
        if Helper.shouldSwapDirection(self, config):
           #or not self.src.is_private:
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

    @property
    def protocol_name(self):
        return IP_PROTOCOLS[self.protocol]

    @property
    def is_one_direction(self):
        return self.answer_flow is None

    @property
    def service(self):
        service = Helper.getService(self.dest_port, self.protocol)
        #logging.info("{} {} {}".format(service, self.dest_port, self.protocol))
        if service is None:
            #if self.dest == MDNS_IP4 or self.dest_raw == "ff02:fb":
            #    service = "mdns"
            #elif self.dest == SSDP_IP4 or self.dest_raw == "ff02:fb":
            #    service = "ssdp"
            #elif self.dest == BROADCAST_IP4:
            #    service = "broadcast"
            if self.is_multicast:
                service = "multicast"
            elif self.protocol in PING_PROTOCOLS:
                service = "ping"
            else:
                service_key = Helper.getServiceKey(self.dest, self.dest_port)
                if service_key in self.config.netflow_incoming_traffic:
                    return self.config.netflow_incoming_traffic[service_key].replace(" ","\\ ").replace(",","\\,")
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
    def __init__(self, config, handler, influxdb ):
        threading.Thread.__init__(self)

        self.is_running = True

        self.config = config

        self.is_enabled = True

        self.connections = []
        self.last_registry = {}
        #self.last_metric_end = time.time() - METRIC_TIMESHIFT

        self.cache = Cache(self.config)

        influxdb.register(self.getMessurements)

        #logging.info(ipaddress.ip_address("192.168.0.50").is_private)
        #logging.info(ipaddress.ip_address("ff02::1:ff6d:914d").is_private)
        #logging.info(ipaddress.ip_address("ff02::1:ff6d:914d").is_multicast)
        #logging.info(ipaddress.ip_address("ff02::1:ff6d:914d").is_global)
        #logging.info(ipaddress.ip_address("185.89.37.91").is_global)

        #logging.info(ipaddress.ip_address("192.168.0.255").is_multicast)
        #logging.info(ipaddress.ip_address("192.168.0.255").is_private)
        #logging.info(ipaddress.ip_address("192.168.0.255").is_global)
        #logging.info(ipaddress.ip_address("192.168.0.255").is_unspecified)
        #logging.info(ipaddress.ip_address("192.168.0.255").is_reserved)
        #logging.info(ipaddress.ip_address("192.168.0.255").is_loopback)
        #logging.info(ipaddress.ip_address("192.168.0.255").is_link_local)
        #logging.info("-----")
        #logging.info(ipaddress.ip_address("192.168.0.1").is_multicast)
        #logging.info(ipaddress.ip_address("192.168.0.1").is_private)
        #logging.info(ipaddress.ip_address("192.168.0.1").is_global)
        #logging.info(ipaddress.ip_address("192.168.0.1").is_unspecified)
        #logging.info(ipaddress.ip_address("192.168.0.1").is_reserved)
        #logging.info(ipaddress.ip_address("192.168.0.1").is_loopback)
        #logging.info(ipaddress.ip_address("192.168.0.1").is_link_local)

        #print(self.resolveLocation(ipaddress.ip_address("185.89.37.91")))

        #print(self.resolveLocation(ipaddress.ip_address("185.89.37.91")))
        #print(self.resolveLocation(ipaddress.ip_address("40.77.167.196")))
        #print(self.resolveLocation(ipaddress.ip_address("80.158.67.40")))
        #print(self.resolveLocation(ipaddress.ip_address("192.168.0.50")))
        #print(self.resolveLocation(ipaddress.ip_address("ff02::1:ff6d:914d")))
        #print(self.cache.getLocation(ipaddress.ip_address("239.255.255.250")))

    def terminate(self):
        self.cache.terminate()
        self.is_running = False

    def start(self):
        self.cache.start()
        super().start()

    def run(self):
        if self.config.netflow_bind_ip is None:
            return

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

    def getMessurements(self):
        messurements = []

        #start = time.time()
        #logging.info("PROCESSING")
        #pr = cProfile.Profile()
        #pr.enable()

        registry = {}
        for con in list(self.connections):
            if con.skipped:
                continue

            timestamp = con.request_ts

            # most flows are already 60 seconds old when they are delivered (flow expire config in softflowd)
            timestamp -= METRIC_TIMESHIFT

            #if timestamp < self.last_metric_end:
            #    #logging.info("fix {} by {}".format(con.answer_flow is not None, int(self.last_metric_end + 1) - timestamp))
            #    timestamp = int(self.last_metric_end + 1)

            _location = con.location

            label = []

            extern_ip = con.src if con.src.is_global else con.dest
            extern_hostname = con.src_hostname if con.src.is_global else con.dest_hostname
            intern_ip = con.dest if con.src.is_global else con.src
            intern_hostname = con.dest_hostname if con.src.is_global else con.src_hostname

            label.append("intern_ip={}".format(intern_ip))
            label.append("intern_host={}".format(intern_hostname))

            label.append("extern_ip={}".format(extern_ip))
            label.append("extern_host={}".format(extern_hostname))
            extern_group = extern_hostname
            for provider in ["amazonaws.com","awsglobalaccelerator.com","cloudfront.net","akamaitechnologies.com","googleusercontent.com"]:
                if provider in extern_hostname:
                    extern_group = "*.{}".format(provider)
                    break
            label.append("extern_group={}".format(extern_group))

            label.append("direction={}".format("incoming" if con.src.is_global else "outgoing"))

            service = con.service
            if service == "unknown" and "speedtest" in extern_hostname:
                service = "speedtest"
            label.append("service={}".format(service))
            label.append("port={}".format(con.dest_port))
            label.append("protocol={}".format(con.protocol_name))
            #label.append("size={}".format(con.size))
            #label.append("duration={}".format(con.duration))
            #label.append("packets={}".format(con.packages))

            label.append("location_country_name={}".format(_location["location_country_name"]))
            label.append("location_country_code={}".format(_location["location_country_code"]))
            label.append("location_city={}".format(_location["location_city"]))
            label.append("location_zip={}".format(_location["location_zip"]))
            label.append("location_lat={}".format(_location["location_lat"]))
            label.append("location_lon={}".format(_location["location_lon"]))

            label.append("ip_type={}".format(con.ip_type))
            #label.append("oneway={}".format(1 if con.is_one_direction else 0))

            #logging.info("SRC: {} {} {}".format(con.src, con.src_hostname,src_location))
            #logging.info("DEST: {} {} {}".format(con.dest, con.dest_hostname,dest_location))

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

        #end = time.time()
        #logging.info("FINISHED in {} seconds".format(end-start))
        #pr.disable()
        #s = io.StringIO()
        #sortby = SortKey.CUMULATIVE
        #ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
        #ps.print_stats()
        #logging.info(s.getvalue())

        counter_values = self.cache.getCountStats()
        logging.info("Cache: LOCATION [fetch: {}, cache {}/{}], HOSTNAME [fetch: {}, cache {}/{}]".format(counter_values["location_fetch"], counter_values["location_cache"], self.cache.getLocationSize(), counter_values["hostname_fetch"], counter_values["hostname_cache"], self.cache.getHostnameSize()))

        #logging.info(messurements)

        #self.last_metric_end = time.time() - METRIC_TIMESHIFT

        return messurements

    def getStateMetrics(self):
        return [
            "system_service_process{{type=\"netflow_processor\",}} {}".format("1" if self.is_running else "0"),
            "system_service_process{{type=\"netflow_cache\",}} {}".format("1" if self.cache.isRunning() else "0"),
            "system_service_state{{type=\"netflow_ip2location\",}} {}".format("1" if self.cache.getState() else "0"),
        ]
