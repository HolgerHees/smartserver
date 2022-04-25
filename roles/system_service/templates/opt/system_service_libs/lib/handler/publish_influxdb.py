import threading
import logging
import requests

from lib.handler import _handler
from lib.dto.group import Group
from lib.dto.connection_stat import ConnectionStat


class InfluxDBHandler(): 
    def __init__(self):
        pass

class InfluxDBPublisher(_handler.Handler): 
    def __init__(self, config, cache ):
        super().__init__()
      
        self.is_running = True
      
        self.config = config
        self.cache = cache
        
        self.condition = threading.Condition()
        self.thread = threading.Thread(target=self._processStats, args=())

    def start(self):
        self.thread.start()
        
    def terminate(self):
        with self.condition:
            self.is_running = False
            self.condition.notifyAll()
        
    def _processStats(self):
        while self.is_running:
            try:
                messurements = self._collectMessurements()
                self._submitMessurements(messurements)
            except requests.exceptions.ConnectionError:
                logging.warning("InfluxDB currently not available. Will 15 seconds")
                
            with self.condition:
                self.condition.wait(self.config.influxdb_publish_interval)
                
    def _collectMessurements(self):
        messurements = []
        
        devices = self.cache.getDevices()
        
        for stat in list(filter(lambda s: type(s) is ConnectionStat, self.cache.getStats() )):
            device = stat.getUnlockedDevice()

            if device is None or device.getIP() is None:
                continue
            
            if device.supportsWifi():
                
                band = "none"
                for gid in device.getGIDs():
                    group = self.cache.getUnlockedGroup(gid)
                    if group is not None and group.getType() == Group.WIFI:
                        band = group.getDetail("band")
                
                if stat.getDetail("signal") is not None:
                    messurement = "network_signal,ip={},band={} value={}".format(device.getIP(),band,stat.getDetail("signal"))
                else:
                    messurement = "network_signal,ip={},band={} value=0".format(device.getIP(),band)
                messurements.append(messurement)
                
            if stat.getInAvg() is not None or stat.getOutAvg() is not None:
                if stat.getInAvg() is not None:
                    messurements.append("network_in_avg,ip={} value={}".format(device.getIP(),stat.getInAvg()))
                if stat.getOutAvg() is not None:
                    messurements.append("network_out_avg,ip={} value={}".format(device.getIP(),stat.getOutAvg()))
                messurements.append("network_total_avg,ip={} value={}".format(device.getIP(),stat.getInAvg() + stat.getOutAvg()))
                
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
