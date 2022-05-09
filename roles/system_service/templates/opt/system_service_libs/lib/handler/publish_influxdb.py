import logging
import requests
import time

from lib.handler import _handler
from lib.dto.group import Group
from lib.dto.connection_stat import ConnectionStat


class InfluxDBHandler(): 
    def __init__(self):
        pass

class InfluxDBPublisher(_handler.Handler): 
    def __init__(self, config, cache ):
        super().__init__()
      
        self.config = config
        self.cache = cache

    def _run(self):
        while self._isRunning():
            try:
                if self._isSuspended():
                    self._confirmSuspended()
                    
                try:
                    messurements = self._collectMessurements()
                    self._submitMessurements(messurements)
                except requests.exceptions.ConnectionError:
                    logging.warning("InfluxDB currently not available. Will 15 retry in seconds")
                
                self._wait(self.config.influxdb_publish_interval)

            except Exception as e:
                timeout = self._handleUnexpectedException(e)
                self._sleep(timeout)
                
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
                    messurements.append("network_signal,ip={},band={} value={}".format(device.getIP(),data.getConnectionDetail("band"), data.getDetail("signal")))
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
        
        #logging.info(messurements)
        logging.info("Submit {} messurements".format(len(messurements)))
        
        #logging.info(messurements)
        headers = {'Authorization': "Token {}".format(self.config.influxdb_token)}
        r = requests.post( "{}/write?db={}&rp=autogen&precision=s&consistency=one".format(self.config.influxdb_rest,self.config.influxdb_database), headers=headers, data="\n".join(messurements))
        if r.status_code != 204:
            msg = "Wrong status code: {}".format(r.status_code)
            logging.error(msg)
            raise requests.exceptions.ConnectionError(msg)
