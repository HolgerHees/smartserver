import threading
import logging
import requests

from lib.handler import _handler
from lib.dto.group import Group


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
                timeout = 60
            except requests.exceptions.ConnectionError:
                logging.warning("InfluxDB currently not available. Will 15 seconds")
                timeout = 60
                
            with self.condition:
                self.condition.wait(timeout)
                
    def _collectMessurements(self):
        messurements = []
        
        for stat in list(self.cache.getStats()):
            if stat.getInterface() is not None:
                continue
            
            mac = stat.getMAC()
            device = self.cache.getUnlockedDevice(mac)
            if device.getIP() is None:
                continue
            
            if device.supportsWifi():
                
                band = "none"
                for gid in device.getGIDs():
                    group = self.cache.getUnlockedGroup(gid)
                    if group is not None and group.getType() == Group.WIFI:
                        band = group.getDetail("band")
                
                signal = stat.getDetail("signal")
                if signal is not None:
                    messurement = "network_signal,ip={},band={} value={}".format(device.getIP(),band,signal)
                else:
                    messurement = "network_signal,ip={},band={} value=0".format(device.getIP(),band)
                messurements.append(messurement)
                
            messurements.append("network_in_avg,ip={} value={}".format(device.getIP(),stat.getInAvg()))
            messurements.append("network_out_avg,ip={} value={}".format(device.getIP(),stat.getOutAvg()))
            messurements.append("network_total_avg,ip={} value={}".format(device.getIP(),stat.getInAvg() + stat.getOutAvg()))
                
        return messurements

    def _submitMessurements(self, messurements):
        if len(messurements) == 0:
            return
        
        logging.info("Submit {} messurements".format(len(messurements)))
        
        #logging.info(messurements)
        headers = {'Authorization': "Token {}".format(self.config.influxdb_token)}
        r = requests.post( "{}/write?db={}&rp=autogen&precision=s&consistency=one".format(self.config.influxdb_rest,self.config.influxdb_database), headers=headers, data="\n".join(messurements))
        if r.status_code != 204:
            msg = "Wrong status code: {}".format(r.status_code)
            logging.error(msg)
            raise requests.exceptions.ConnectionError(msg)
