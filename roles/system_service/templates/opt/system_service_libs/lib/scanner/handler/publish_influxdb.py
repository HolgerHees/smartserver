import requests
import time

from lib.scanner.handler import _handler
from lib.scanner.dto.group import Group
from lib.scanner.dto.connection_stat import ConnectionStat


class InfluxDBHandler(): 
    def __init__(self):
        pass

class InfluxDBPublisher(_handler.Handler): 
    def __init__(self, config, cache, influxdb ):
        super().__init__(config,cache, False)

        influxdb.register(self.getMessurements)

    def getMessurements(self):
        messurements = []

        devices = self.cache.getDevices()

        for stat in list(filter(lambda s: type(s) is ConnectionStat, self.cache.getStats() )):
            device = stat.getUnlockedDevice()

            if device is None or device.getIP() is None:
                continue

            inAvg = None
            outAvg = None
            for data in stat.getDataList():
                if device.supportsWifi() and data.getDetail("signal") is not None:
                    gid = data.getConnectionDetail("gid")
                    band = self.cache.getUnlockedGroup(gid).getDetail("band")
                    messurements.append("network_signal,ip={},band={} value={}".format(device.getIP(),band, data.getDetail("signal")))
                if data.getInAvg() is not None:
                    if inAvg is None:
                        inAvg = 0
                    inAvg += data.getInAvg()
                if data.getOutAvg() is not None:
                    if outAvg is None:
                        outAvg = 0
                    outAvg += data.getOutAvg()

                if device.getIP() == self.config.default_gateway_ip:
                    for wan_stats in ["wan_type","wan_state"]:
                        wan_stats_value = data.getDetail(wan_stats)
                        if wan_stats_value is not None:
                            messurements.append("network_{} value=\"{}\"".format(wan_stats,wan_stats_value))

            if inAvg is not None or outAvg is not None:
                if inAvg is not None:
                    messurements.append("network_in_avg,ip={} value={}".format(device.getIP(),inAvg))
                if outAvg is not None:
                    messurements.append("network_out_avg,ip={} value={}".format(device.getIP(),outAvg))
                messurements.append("network_total_avg,ip={} value={}".format(device.getIP(),inAvg + outAvg))

        return messurements
