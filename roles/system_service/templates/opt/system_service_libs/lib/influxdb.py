import requests
import time

import logging


class InfluxDB():
    def __init__(self, config ):
      self.config = config

    def submit(self, messurements):
        if len(messurements) == 0:
            return
        
        #Helper.logInfo(messurements)
        headers = {'Authorization': "Token {}".format(self.config.influxdb_token)}
        r = requests.post( "{}/write?db={}&rp=autogen&precision=s&consistency=one".format(self.config.influxdb_rest,self.config.influxdb_database), headers=headers, data="\n".join(messurements))
        if r.status_code != 204:
            msg = "Wrong status code: {}".format(r.status_code)
            logging.error(msg)
            requests.exceptions.ConnectionError(msg)
