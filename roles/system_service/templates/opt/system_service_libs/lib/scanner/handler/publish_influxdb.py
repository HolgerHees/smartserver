import requests
import time

from lib.scanner.handler import _handler
from lib.scanner.dto.group import Group
from lib.scanner.dto.connection_stat import ConnectionStat
from lib.scanner.helper import Helper


class InfluxDBHandler(): 
    def __init__(self):
        pass

class InfluxDBPublisher(_handler.Handler): 
    def __init__(self, config, cache, influxdb ):
        super().__init__(config,cache)

        self.influxdb = influxdb

        self._setServiceMetricState("influxdb", -1)

    def _run(self):
        while self._isRunning():
            if not self._isSuspended():
                try:
                    messurements = self._collectMessurements()
                    self._submitMessurements(messurements)

                    self._setServiceMetricState("influxdb", 1)
                except requests.exceptions.ConnectionError:
                    Helper.logInfo("InfluxDB currently not available. Will retry in {} seconds".format(self.config.influxdb_publish_interval))
                    self._setServiceMetricState("influxdb", 0)
                except Exception as e:
                    self._handleUnexpectedException(e)
                    self._setServiceMetricState("influxdb", -1)

            suspend_timeout = self._getSuspendTimeout()
            if suspend_timeout > 0:
                timeout = suspend_timeout
            else:
                timeout = self.config.influxdb_publish_interval
                
            self._wait(timeout)

    def _collectMessurements(self):
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
                
            if inAvg is not None or outAvg is not None:
                if inAvg is not None:
                    messurements.append("network_in_avg,ip={} value={}".format(device.getIP(),inAvg))
                if outAvg is not None:
                    messurements.append("network_out_avg,ip={} value={}".format(device.getIP(),outAvg))
                messurements.append("network_total_avg,ip={} value={}".format(device.getIP(),inAvg + outAvg))
                
        return messurements

    def _submitMessurements(self, messurements):
        if len(messurements) == 0:
            return
        
        #Helper.logInfo(messurements)
        Helper.logInfo("Submit {} messurements".format(len(messurements)))
        self.influxdb.submit(messurements)
