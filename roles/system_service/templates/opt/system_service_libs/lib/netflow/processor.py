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
    def __init__(self, config, handler ):
        threading.Thread.__init__(self)

        #self.is_running = True
        self.event = threading.Event()

        self.config = config

        self.connections = []

        self.is_enabled = True

        self.last_metric_end = time.time() - METRIC_TIMESHIFT
        self.last_labels = {}

    def terminate(self):
        #self.is_running = False
        self.event.set()

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

            while not self.event.is_set():
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
        finally:
            self.listener.stop()
            self.listener.join()

    def getMetrics(self, is_prometheus):
        last_labels = dict(self.last_labels)

        #f = open("/tmp/netflow.log", "w")
        #now = datetime.now().timestamp()
        registry = {}
        for con in list(self.connections):
            timestamp = int(con.request_ts)

            # we have to wait until all flows arrived, including the ones from cleanup
            #if now - timestamp <= 30:
            #    continue

            # most flows are already 60 seconds old when they are delivered (flow expire config in softflowd)
            timestamp -= METRIC_TIMESHIFT

            if timestamp < self.last_metric_end:
                #logging.info("fix {} by {}".format(con.answer_flow is not None, int(self.last_metric_end + 1) - timestamp))
                timestamp = int(self.last_metric_end + 1)

            label = []
            label.append("protocol=\"{}\"".format(con.protocol_name))
            label.append("service=\"{}\"".format(con.service))
            label.append("port=\"{}\"".format(con.dest_port))
            #label.append("size=\"{}\"".format(con.size))
            #label.append("duration=\"{}\"".format(con.duration))
            #label.append("packets=\"{}\"".format(con.packages))
            label.append("src_ip=\"{}\"".format(con.src))
            label.append("src_host=\"{}\"".format(con.src_hostname))
            label.append("dest_ip=\"{}\"".format(con.dest))
            label.append("dest_host=\"{}\"".format(con.dest_hostname))
            label.append("ip_type=\"{}\"".format(con.ip_type))
            #label.append("oneway=\"{}\"".format(1 if con.is_one_direction else 0))

            label_str = ",".join(label)

            key = label_str
            if key not in registry:
                registry[key] = [label_str, 0, timestamp]
            registry[key][1] += con.size

            if label_str in last_labels:
                del last_labels[label_str]

            if is_prometheus:
                self.connections.remove(con)

        # create 0 traffic metric, if there are no new flows from previous generated traffic metrics
        for last_label_str in last_labels:
            timestamp = last_labels[last_label_str] + PROMETHEUS_INTERVAL
            key = "{} {}".format(last_label_str, timestamp)
            registry[key] = [last_label_str, 0, timestamp]
            #registry[key] = [ con, timestamp, "system_service_netflow_size{{{}}} {} {}".format(label_str, con.size, timestamp) ]

        metrics = []
        labels = {}
        sorted_registry = sorted(registry.values(), key=lambda x: x[2])
        if len(sorted_registry) > 0:
            for data in sorted_registry:
                metrics.append("system_service_netflow_size{{{}}} {} {}000".format(data[0], data[1], data[2]))
                if data[1] > 0:
                    labels[data[0]] = data[2]

                #key = "system_service_netflow_size{{{}}} {}".format(label_str, time_str)
                #if key in check:
                #    logging.error("Douplicate metric {}, TS OLD: {}, TS NEW: {}".format(key, check[key].request_ts, con.request_ts))
                #    logging.error(check[key].request_flow)
                #    logging.error(con.request_flow)
                #check[key] = con

                #metrics.append("system_service_netflow_duration{{{}}} {} {}".format(label_str, con.duration, time_str))
                #metrics.append("system_service_netflow_packets{{{}}} {} {}".format(label_str, con.packages, time_str))
                #metrics.append("system_service_netflow_oneway{{{}}} {} {}".format(label_str, 1 if con.is_one_direction else 0, time_str))

                #con = data[0]
                #if con.src_raw == "134.76.12.6" or con.dest_raw == "134.76.12.6":
                #    logging.info("------------------")
                #    direction = "=>" if con.is_one_direction else "<=>"
                #    info = "{src_host} ({src}) {direction} {dest_host} ({dest})".format(src_host=con.src_hostname, src=con.src, direction=direction, dest_host=con.dest_hostname, dest=con.dest)
                #    msg = "{protocol:<7} | {service:<14} | {size:10} | {info}".format(protocol=con.protocol, service=con.service, size=con.size, info=info)
                #    logging.info(con.request_flow)
                #    logging.info(con.answer_flow)
                #    logging.info(msg)

                #logging.info(msg)
                #if con.is_swapped:
                #    logging.info("--- swapped")

                #if not con.src.is_private:
                #    logging.info(con.request_flow)
                #    logging.info(con.answer_flow)


                #f.write(msg)
                #f.write("\n")
                #f.write(str(con.request_flow))
                #f.write("\n")
                #f.write(str(con.answer_flow))
                #f.write("\n\n")

            #f.close()

            if is_prometheus:
                #self.last_metric_request = time.time()
                self.last_metric_end = time.time() - METRIC_TIMESHIFT
                self.last_labels = labels

        logging.info("Submit {} flows".format(len(metrics)))

        return metrics
