import socket
import contextlib

class Helper():
    @staticmethod
    def getService(port, protocol_name):
        if port is not None and port < 1024:
            with contextlib.suppress(OSError):
                return socket.getservbyport(port, protocol_name)
        return None

    @staticmethod
    def getIncommingService(ip, port, incoming_traffic_config):
        service_key = Helper.getServiceKey(ip, port)
        if service_key in incoming_traffic_config:
            return incoming_traffic_config[service_key]["name"]
        return None

    @staticmethod
    def getServiceKey(ip, port):
        return "{}:{}".format(ip.compressed, port)

class TrafficGroup():
    NORMAL = 'normal'
    OBSERVED = 'observed'
    SCANNING = 'scanning'
    INTRUDED = 'intruded'

    PRIORITY = {
        "-": 0,
        NORMAL: 1,
        OBSERVED: 2,
        SCANNING: 3,
        INTRUDED: 4
    }
