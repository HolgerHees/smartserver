import requests
import time
import logging

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

        for stat in list(filter(lambda s: type(s) is ConnectionStat, self.cache.getStats() )):
            if stat.getTargetMAC() == self.cache.getWanMAC():
                for data in stat.getDataList():
                    wan_values = []
                    for wan_stats in ["wan_type","wan_state"]:
                        wan_stats_value = data.getDetail(wan_stats)
                        if wan_stats_value is not None:
                            wan_values.append("{}=\"{}\"".format(wan_stats[4:],wan_stats_value))
                    messurements.append("network_wan {}".format(",".join(wan_values)))
            else:
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
                if inAvg is not None or outAvg is not None:
                    wan_values = []
                    if inAvg is not None:
                        wan_values.append("in_avg={}".format(inAvg))
                        #messurements.append("network_in_avg,ip={} value={}".format(device.getIP(),inAvg))
                    if outAvg is not None:
                        wan_values.append("out_avg={}".format(outAvg))
                        #messurements.append("network_out_avg,ip={} value={}".format(device.getIP(),outAvg))
                    #wan_values.append("total_avg={}".format(outAvg))
                    #messurements.append("network_total_avg,ip={} value={}".format(device.getIP(),inAvg + outAvg))
                    messurements.append("network_traffic,ip={} {}".format(device.getIP(),",".join(wan_values)))

        #for messurement in messurements:
        #    logging.info(messurement)

        return messurements
