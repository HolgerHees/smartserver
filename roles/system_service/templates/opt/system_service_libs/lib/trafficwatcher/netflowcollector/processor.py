#import netflow # https://github.com/bitkeks/python-netflow-v9-softflowd
import queue
import threading
import logging
import traceback
import time
from datetime import datetime, timezone

import ipaddress

import cProfile, pstats, io
from pstats import SortKey

from .collector import ThreadedNetFlowListener

from netflow.v9 import V9OptionsTemplateRecord, V9TemplateRecord

from lib.trafficwatcher.helper.helper import TrafficGroup, Helper as TrafficHelper

IP_protocolIdentifierS = {
    1: "icmp",
    2: "igmp",
    6: "tcp",
    17: "udp",
    58: "icmpv6"
}

IP_PING_protocolIdentifierS = [1,58]
IP_DATA_protocolIdentifierS = [6,17]

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

class Helper():
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

        #if connection.protocol in IP_PING_protocolIdentifierS:
        #    return srcIsExternal
        #    #if Helper.checkFlag(connection.request_icmp_flags, ICMP_TYPES["ECHO_REPLY"]): # is an answer flow
        #    #    return True
        #    #if Helper.checkFlag(connection.request_icmp_flags, ICMP_TYPES["TIME_REPLY"]): # is an answer flow
        #    #    return True
        #    #if Helper.checkFlag(connection.request_icmp_flags, ICMP_TYPES["EXTENDED_ECHO_REPLY"]): # is an answer flow
        #    #    return True
        #    #if Helper.checkFlag(connection.request_icmp_flags, ICMP_TYPES["ECHO_REQUEST"]): # can only happen from inside, because gateway firewall is blocking/nat traffic
        #    #    return True
        if connection.protocol in IP_DATA_protocolIdentifierS:
            #if connection.answer_tcp_flags is not None:
            #    if Helper.checkFlag(connection.request_tcp_flags, TCP_FLAG_TYPES["ACK"]): # is an answer flow
            #        return True
            if connection.src_port is not None and connection.dest_port is not None:
                # https://en.wikipedia.org/wiki/list_of_tcp_and_udp_port_numbers
                if connection.src_port < 1024 and connection.dest_port >= 1024: # system ports
                    return True
                elif connection.dest_port < 1024 and connection.src_port >= 1024: # system ports
                    return False
                #elif connection.src_port < 49152 and connection.dest_port >= 49152: # registered ports
                #    return True
                #elif connection.dest_port < 49152 and connection.src_port >= 49152: # registered ports
                #    return False

                if config.netflow_incoming_traffic:
                    if srcIsExternal:
                        return TrafficHelper.getServiceKey(connection.dest, connection.dest_port) not in config.netflow_incoming_traffic
                    else:
                        return TrafficHelper.getServiceKey(connection.src, connection.src_port) in config.netflow_incoming_traffic

        return srcIsExternal

class Connection:
    def __init__(self, gateway_base_time, request_ts, request_flow, answer_flow, config, ipcache):
        self.connection_type = "netflow"

        if gateway_base_time > 0:
            #_diff = ( request_flow["flowEndSysUpTime"] - request_flow["flowStartSysUpTime"]) / 1000
            self.start_timestamp = ( gateway_base_time + request_flow["flowStartSysUpTime"] ) / 1000
            self.end_timestamp = ( gateway_base_time + request_flow["flowEndSysUpTime"] ) / 1000
            if request_ts - self.start_timestamp > 600:
                # can happen after 2982 days uptime
                logging.error("FALLBACK happens {} {}. Maybe overflow of datatype unsigned 32bit for 'flowStartSysUpTime'".format(datetime.fromtimestamp(self.start_timestamp), datetime.fromtimestamp(request_ts)))
                self.start_timestamp = self.end_timestamp = 0
            #logging.info("{} => {}".format(datetime.fromtimestamp(self.start_timestamp), datetime.fromtimestamp(_timestamp)))
        else:
            self.start_timestamp = self.end_timestamp = 0

        if self.start_timestamp == 0:
            # METRIC_TIMESHIFT => most flows are already 60 seconds old when they are delivered (flow expire config in softflowd)
            self.start_timestamp = request_ts - ( request_flow["flowEndSysUpTime"] - request_flow["flowStartSysUpTime"]) / 1000  - METRIC_TIMESHIFT
            self.end_timestamp = request_ts
        #self.timestamp = request_ts - METRIC_TIMESHIFT
        #logging.info("{} => {} : {}".format(datetime.fromtimestamp(request_ts - METRIC_TIMESHIFT), datetime.fromtimestamp(self.timestamp),_diff))

        # https://www.iana.org/assignments/ipfix/ipfix.xhtml
        # TODO flowDirection

        self.request_flow = request_flow
        self.answer_flow = answer_flow

        self.config = config
        self.ipcache = ipcache

        self.protocol = self.request_flow["protocolIdentifier"]

        if request_flow.get('ipVersion') == 4 or 'sourceIPv4Address' in request_flow or 'destinationIPv4Address' in request_flow:
            self.src_raw = request_flow['sourceIPv4Address']
            self.src = ipaddress.ip_address(self.src_raw)
            self.dest_raw = request_flow['destinationIPv4Address']
            self.dest = ipaddress.ip_address(self.dest_raw)
            self.ip_type = "v4"

            self.request_icmp_flags = self.request_flow['icmpTypeCodeIPv4'] if 'icmpTypeCodeIPv4' in self.request_flow else None
            self.answer_icmp_flags = self.answer_flow['icmpTypeCodeIPv4'] if self.answer_flow is not None and 'icmpTypeCodeIPv4' in self.answer_flow else None
        else:
            self.src_raw = request_flow['sourceIPv6Address']
            self.src = ipaddress.ip_address(self.src_raw)
            self.dest_raw = request_flow['destinationIPv6Address']
            self.dest = ipaddress.ip_address(self.dest_raw)
            self.ip_type = "v6"

            self.request_icmp_flags = self.request_flow['icmpTypeCodeIPv6'] if 'icmpTypeCodeIPv6' in self.request_flow else None
            self.answer_icmp_flags = self.answer_flow['icmpTypeCodeIPv6'] if self.answer_flow is not None and 'icmpTypeCodeIPv6' in self.answer_flow else None

        self.src_port = self.request_flow['sourceTransportPort'] if 'sourceTransportPort' in self.request_flow else None
        self.dest_port = self.request_flow['destinationTransportPort'] if 'destinationTransportPort' in self.request_flow else None

        self.request_tcp_flags = self.request_flow['tcpControlBits'] if 'tcpControlBits' in self.request_flow else None
        self.answer_tcp_flags = self.answer_flow['tcpControlBits'] if self.answer_flow is not None and 'tcpControlBits' in self.answer_flow else None

        # swap direction
        if Helper.shouldSwapDirection(self, config, ipcache):
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

        self.tcp_flags = self.request_tcp_flags if self.request_tcp_flags is not None else 0
        self.size = self.request_flow['octetDeltaCount'] + ( self.answer_flow['octetDeltaCount']  if self.answer_flow is not None else 0 )
        self.packages = self.request_flow["packetDeltaCount"] + ( self.answer_flow["packetDeltaCount"] if self.answer_flow is not None else 0 )

        # Duration is given in milliseconds
        self.duration = self.request_flow['flowEndSysUpTime'] - self.request_flow['flowStartSysUpTime']
        if self.duration < 0:
            # 32 bit int has its limits. Handling overflow here
            # TODO: Should be handled in the collection phase
            self.duration = (2 ** 32 - self.request_flow['flowStartSysUpTime']) + self.request_flow['flowEndSysUpTime']

        is_multicast = True if self.dest.is_multicast or self.src.is_multicast else False
        is_broadcast = True if self.dest.compressed.endswith(".255") or self.src.compressed.endswith(".255") else False
        is_other_special = True if self.dest.is_unspecified or self.src.is_unspecified else False

        self.skipped = is_multicast or is_broadcast or is_other_special

        if not self.skipped:
            self._location = self.ipcache.getLocation(self.src if self.src.is_global else self.dest, True)

            self._src_hostname = self.ipcache.getHostname(self.src, True)
            self._dest_hostname = self.ipcache.getHostname(self.dest, True)

            self.src_is_external = self.ipcache.isExternal(self.src)

            if self.protocol in IP_PING_protocolIdentifierS:
                if Helper.checkFlag(self.request_icmp_flags, ICMP_TYPES["ECHO_REQUEST"]):
                    self.service = "ping"
                else:
                    self.service = "icmp"
            else:
                self.service = TrafficHelper.getService(self.dest_port, IP_protocolIdentifierS[self.protocol]) if self.protocol in IP_DATA_protocolIdentifierS else None
                if self.service is None:
                    self.service = TrafficHelper.getIncommingService(self.dest, self.dest_port, self.config.netflow_incoming_traffic)
                    if self.service is None:
                        if "speedtest" in self.dest_hostname:
                            self.service = "speedtest"
                        else:
                            self.service = "unknown"

            #if self.dest_port is None or self.service == "unknown":
            #    logging.info("{} {} {}".format(self.src_port,self.dest_port,self.service))
            #    logging.info("{} {}".format(self.protocol,self.request_icmp_flags))
            #    logging.info(str(self.request_flow))


        #if self.src.is_global and self.dest_port not in [80,10114,51828,51829]:
        #    logging.error("WIRED")
        #    logging.error(self.request_flow)
        #    logging.error(self.is_swapped)
        #elif self.is_swapped:
        #    logging.info("SWAPPED {} => {}".format(self.src,self.dest))


#Apr 03 15:10:49 marvin system_service[3445]: [INFO] - [lib.netflow.processor:121] - {'sourceIPv4Address': '34.158.0.131', 'destinationIPv4Address': '192.168.0.108', 'flowStartSysUpTime': 24968747, 'flowEndSysUpTime': 25030465, 'IN_BYTES': 441, 'IN_PKTS': 7, 'INPUT_SNMP': 0, 'OUTPUT_SNMP': 0, 'sourceTransportPort': 4070, 'destinationTransportPort': 48096, 'protocolIdentifier': 6, 'TCP_FLAGS': 24, 'ipVersion': 4, 'SRC_TOS': 0}
#Apr 03 15:10:49 marvin system_service[3445]: [INFO] - [lib.netflow.processor:122] - False

    def getDebugData(self):
        _request_flow = self.request_flow.copy()
        _request_flow["src"] = ipaddress.ip_address(_request_flow["sourceIPv4Address"]).compressed
        del _request_flow['sourceIPv4Address']
        port = _request_flow['sourceTransportPort'] if 'sourceTransportPort' in _request_flow else None
        if port:
            _request_flow["src"] = "{}:{}".format(_request_flow["src"], port)
            del _request_flow['sourceTransportPort']

        _request_flow["dest"] = ipaddress.ip_address(_request_flow["destinationIPv4Address"]).compressed
        del _request_flow['destinationIPv4Address']
        port = _request_flow['destinationTransportPort'] if 'destinationTransportPort' in _request_flow else None
        if port:
            _request_flow["dest"] = "{}:{}".format(_request_flow["dest"], port)
            del _request_flow['destinationTransportPort']

        for key in ["flowStartSysUpTime", "flowEndSysUpTime", "ingressInterface", "egressInterface", "octetDeltaCount", "packetDeltaCount", "ipClassOfService", "ipVersion"]:
            del _request_flow[key]
            #if data["response"] is not None:
            #    del data["response"][key]

        return " - answer: {} - {}".format("yes" if self.answer_flow is not None else "no", _request_flow)

    def formatTCPFlags(self, tcp_flags):
        flags = []
        if tcp_flags > 0:
            for flag, name in TCP_FLAGS.items():
                if flag & tcp_flags == flag:
                    flags.append(name)
        return "|".join(flags) if len(flags) > 0 else ""

    @staticmethod
    def mergeData(data, flow):
        if TrafficGroup.PRIORITY[data["state_tags"]["group"]] < TrafficGroup.PRIORITY[flow["state_tags"]["traffic_group"]]:
            data["state_tags"]["group"] = flow["state_tags"]["traffic_group"]

        if TrafficGroup.PRIORITY[data["state_tags"]["traffic_group"]] < TrafficGroup.PRIORITY[flow["state_tags"]["traffic_group"]]:
            data["state_tags"]["traffic_group"] = flow["state_tags"]["traffic_group"]

        if "traffic_size" in flow["values"]:
            if "traffic_size" in data["values"]:
                data["values"]["traffic_size"] += flow["values"]["traffic_size"]
            else:
                data["values"]["traffic_size"] = flow["values"]["traffic_size"]

        if "traffic_count" in flow["values"]:
            if "traffic_count" in data["values"]:
                data["values"]["traffic_count"] += flow["values"]["traffic_count"]
            else:
                data["values"]["traffic_count"] = flow["values"]["traffic_count"]

        if "tcp_flags" in flow["values"]:
            if "tcp_flags" in data["values"]:
                data["values"]["tcp_flags"][0] |= flow["values"]["tcp_flags"][0]
            else:
                data["values"]["tcp_flags"] = flow["values"]["tcp_flags"]

    def applyData(self, data, traffic_group):
        data["state_tags"]["group"] = traffic_group
        data["state_tags"]["traffic_group"] = traffic_group
        data["values"]["traffic_size"] = self.size
        data["values"]["traffic_count"] = 1
        data["values"]["tcp_flags"] = [ self.tcp_flags, self.formatTCPFlags ]

    def getTrafficGroup(self, blocklist_name):
        if blocklist_name:
            if blocklist_name == "unknown":
                return TrafficGroup.OBSERVED
            elif self.src_is_external:
                return TrafficGroup.SCANNING
            else:
                return TrafficGroup.OBSERVED if self.service == "icmp" else TrafficGroup.INTRUDED
        return TrafficGroup.NORMAL

    def isFilteredTrafficGroup(self, traffic_group):
        return False

    @property
    def protocol_name(self):
        return IP_protocolIdentifierS[self.protocol]

    @property
    def is_one_direction(self):
        return self.answer_flow is None

    @property
    def src_hostname(self):
        return self._src_hostname if self._src_hostname is not None else self.ipcache.getHostname(self.src, False)

    @property
    def dest_hostname(self):
        return self._dest_hostname if self._dest_hostname is not None else self.ipcache.getHostname(self.dest, False)

    @property
    def location(self):
        return self._location if self._location is not None else self.ipcache.getLocation(self.src if self.src.is_global else self.dest, False)

class Processor(threading.Thread):
    def __init__(self, config, watcher, ipcache ):
        threading.Thread.__init__(self)

        self.is_running = False

        self.config = config

        self.is_enabled = True

        self.watcher = watcher
        self.ipcache = ipcache

        #_ip = "192.168.0.1"
        #ip = ipaddress.IPv4Address(_ip)
        #logging.info("IP: {}, is_multicast: {}, is_private: {}, is_global: {}, is_unspecified: {}, is_reserved: {}, is_loopback: {}, is_link_local: {}".format(_ip, ip.is_multicast, ip.is_private, ip.is_global, ip.is_unspecified, ip.is_reserved, ip.is_loopback, ip.is_link_local))
        #_ip = "8.8.8.8"
        #ip = ipaddress.IPv4Address(_ip)
        #logging.info("IP: {}, is_multicast: {}, is_private: {}, is_global: {}, is_unspecified: {}, is_reserved: {}, is_loopback: {}, is_link_local: {}".format(_ip, ip.is_multicast, ip.is_private, ip.is_global, ip.is_unspecified, ip.is_reserved, ip.is_loopback, ip.is_link_local))
        #_ip = "127.0.0.1"
        #ip = ipaddress.IPv4Address(_ip)
        #logging.info("IP: {}, is_multicast: {}, is_private: {}, is_global: {}, is_unspecified: {}, is_reserved: {}, is_loopback: {}, is_link_local: {}".format(_ip, ip.is_multicast, ip.is_private, ip.is_global, ip.is_unspecified, ip.is_reserved, ip.is_loopback, ip.is_link_local))
        #_ip = "0.0.0.0"
        #ip = ipaddress.IPv4Address(_ip)
        #logging.info("IP: {}, is_multicast: {}, is_private: {}, is_global: {}, is_unspecified: {}, is_reserved: {}, is_loopback: {}, is_link_local: {}".format(_ip, ip.is_multicast, ip.is_private, ip.is_global, ip.is_unspecified, ip.is_reserved, ip.is_loopback, ip.is_link_local))
        #_ip = "8.8.8.255"
        #ip = ipaddress.IPv4Address(_ip)
        #logging.info("IP: {}, is_multicast: {}, is_private: {}, is_global: {}, is_unspecified: {}, is_reserved: {}, is_loopback: {}, is_link_local: {}".format(_ip, ip.is_multicast, ip.is_private, ip.is_global, ip.is_unspecified, ip.is_reserved, ip.is_loopback, ip.is_link_local))

    def terminate(self):
        self.is_running = False

    def start(self):
        self.is_running = True
        super().start()

    def run(self):
        if self.config.netflow_bind_ip is None:
            return

        logging.info("Netflow processor started")

        #collectorLogger.setLevel(logging.DEBUG)
        #collectorCS.setLevel(logging.DEBUG)

        self.listener = ThreadedNetFlowListener(self.config.netflow_bind_ip, self.config.netflow_bind_port)
        self.listener.start()

        self.gateway_base_time = 0

        try:
            pending = {}
            last_cleanup = time.time()

            while self.is_running:
                connections = []
                try:
                    ts, client, export = self.listener.get(timeout=0.5)

                    #flows = []
                    #for f in export.flows:
                    #    flows.append(f.data)

                    if not self.is_enabled:
                        #logging.info("Netflow flows: {}".format(len(flows)))
                        continue

                    if export.header.version != 10:
                        logging.error("Unsupported netflow version {}. Only version 10 is supported.".format(export.header.version))
                        continue

                    #if export.contains_new_templates:
                    #for key, template in export.templates.items():

                    #    if isinstance(template, V9TemplateRecord):
                    #        logging.info(str(key))
                    #        #logging.info(str(template))
                    #        for field in template.fields:
                    #            logging.info("{}".format(field))
                    #    elif isinstance(template, V9OptionsTemplateRecord):
                    #        logging.info(str(key))
                    #        for key,field in template.option_fields.items():
                    #            logging.info("{} {}".format(key, field))

                    #for id, template in export.templates.items():
                    #    for field in template:
                    # #        logging.info(str(field))

                    #for flow in sorted(flows, key=lambda x: x["flowStartSysUpTime"]):
                    for f in export.flows:
                        flow = f.data
                        if "systemInitTimeMilliseconds" in flow:
                            self.gateway_base_time = flow["systemInitTimeMilliseconds"]

                        # ignore non traffic related flows
                        if "flowStartSysUpTime" not in flow:
                            #logging.info(flow)
                            continue

                        first_switched = flow["flowStartSysUpTime"]

                        if "protocolIdentifier" not in flow:
                            if "icmpTypeCodeIPv4" in flow or "icmpTypeCodeIPv6" in flow:
                                flow["protocolIdentifier"] = 1
                            elif "igmpType" in flow:
                                flow["protocolIdentifier"] = 2
                            else:
                                flow["protocolIdentifier"] = 0

                        if flow["protocolIdentifier"] not in IP_protocolIdentifierS:
                            flow["protocolIdentifier"] = 17
                            #logging.info("Unknown protocol {}".format(flow["protocolIdentifier"]))
                            #logging.info(flow)
                            #continue

                        #if first_switched - 1 in pending:
                        #    # TODO: handle fitting, yet mismatching (here: 1 second) pairs
                        #    pass

                        # Find the peer for this connection
                        if "sourceIPv4Address" in flow or flow.get("ipVersion") == 4:
                            src_addr = flow["sourceIPv4Address"]
                            dest_addr = flow["destinationIPv4Address"]
                        else:
                            src_addr = flow["sourceIPv6Address"]
                            dest_addr = flow["destinationIPv6Address"]

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
                                    con = Connection(self.gateway_base_time, request_ts, request_flow, None, self.config, self.ipcache)
                                    connections.append(con)
                                pending[request_key] = [ flow, ts ]
                                continue

                        #logging.info("{}".format(peer_flow))
                        #logging.info("{}".format(flow))
                        #logging.info("---------")

                        #raise Exception

                        con = Connection(self.gateway_base_time, request_ts, request_flow, answer_flow, self.config, self.ipcache)
                        connections.append(con)

                    #self.getMetrics()

                except queue.Empty:
                    pass
                except Exception:
                    logging.error(traceback.format_exc())

                now = time.time()
                if now - last_cleanup >= 1:
                    for request_key in list(pending.keys()):
                        request_flow, request_ts = pending[request_key]
                        if ts - request_ts > 15:
                            con = Connection(self.gateway_base_time, request_ts, request_flow, None, self.config, self.ipcache)
                            connections.append(con)
                            del pending[request_key]
                    last_cleanup = now

                self.watcher.addConnections(connections)

            logging.info("Netflow processor stopped")
        except Exception:
            logging.error(traceback.format_exc())
            self.is_running = False
        finally:
            self.listener.stop()
            self.listener.join()

    def getStateMetrics(self):
        return [ "system_service_process{{type=\"trafficwatcher.netflowcollector\",}} {}".format("1" if self.is_running else "0") ]
