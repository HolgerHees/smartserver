import requests
import time
import threading
import traceback

import logging


class InfluxDB(threading.Thread):
    def __init__(self, config ):
      threading.Thread.__init__(self)

      self.event = threading.Event()

      self.config = config

      self.callbacks = []

      self.state_metrics = -1

    def getStateMetrics(self):
        return ["system_service_state{{type=\"influxdb\"}} {}".format(self.state_metrics)]

    def terminate(self):
        #self.is_running = False
        self.event.set()

    def run(self):
        while not self.event.is_set():
            messurements = []
            try:
                for callback in self.callbacks:
                    messurements += callback()
            except Exception as e:
                logging.error("{} got unexpected exception. Will retry in {} seconds".format(self.config.influxdb_publish_interval))
                logging.error(traceback.format_exc())
                self.state_metrics = -1

            self.state_metrics = self.submit(messurements)

            self.event.wait(self.config.influxdb_publish_interval)
            #self.event.clear()

    def register(self, callback):
        self.callbacks.append(callback)

    def submit(self, messurements):
        try:
            if len(messurements) == 0:
                return

            logging.info("Submit {} messurements".format(len(messurements)))

            headers = {'Authorization': "Token {}".format(self.config.influxdb_token)}
            r = requests.post( "{}/write?db={}&rp=autogen&precision=s&consistency=one".format(self.config.influxdb_rest,self.config.influxdb_database), headers=headers, data="\n".join(messurements))
            if r.status_code != 204:
                msg = "Wrong status code: {}".format(r.status_code)
                logging.error(msg)
                raise requests.exceptions.ConnectionError(msg)
            return 1
        except requests.exceptions.ConnectionError:
            logging.info("InfluxDB currently not available. Will retry in {} seconds".format(self.config.influxdb_publish_interval))
            return 0
        except Exception as e:
            logging.error("{} got unexpected exception. Will retry in {} seconds".format(self.config.influxdb_publish_interval))
            logging.error(traceback.format_exc())
            return -1
