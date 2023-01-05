import requests
import time
import threading
import traceback
import urllib.parse
import json

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
                self.state_metrics = self.submit(messurements)
            except Exception as e:
                logging.error("{} got unexpected exception. Will retry in {} seconds".format(self.config.influxdb_publish_interval))
                logging.error(traceback.format_exc())
                self.state_metrics = -1

            self.event.wait(self.config.influxdb_publish_interval)
            #self.event.clear()

    def register(self, callback):
        self.callbacks.append(callback)

    def get(self, messurements):
        #curl -G 'http://localhost:8086/query?pretty=true' --data-urlencode "db=mydb" --data-urlencode "q=SELECT \"value\" FROM \"cpu_load_short\" WHERE \"region\"='us-west';SELECT count(\"value\") FROM \"cpu_load_short\" WHERE \"region\"='us-west'"

        queries = []
        for messurement in messurements:
            queries.append("SELECT last(\"value\") FROM \"{}\"".format(messurement))

        headers = {'Authorization': "Token {}".format(self.config.influxdb_token), "Content-Type": "application/vnd.influxql"}
        url = "{}/query?pretty=true&db={}&rp=autogen&q={}".format(self.config.influxdb_rest,self.config.influxdb_database, urllib.parse.quote(";".join(queries)))

        r = requests.get( url, headers=headers)

        if r.status_code != 200:
            logging.info("Wrong status code {} for query {}".format(r.status_code, url))
            return None

        try:
            values = {}
            data = json.loads(r.text)

            #logging.info(data)

            for result in data["results"]:
                if "series" not in result or len(result["series"]) < 1 or len(result["series"][0]["values"]) < 1:
                    continue

                values[result["series"][0]["name"]] = result["series"][0]["values"][0][1]
            return values

        except Exception as e:
            logging.error("{} got unexpected exception".format(e, self.config.influxdb_publish_interval))
            logging.error(traceback.format_exc())
            return None

    def submit(self, messurements):
        try:
            if len(messurements) == 0:
                return 1

            logging.info("Submit {} messurements".format(len(messurements)))

            headers = {'Authorization': "Token {}".format(self.config.influxdb_token)}
            url = "{}/write?db={}&rp=autogen&precision=ms&consistency=one".format(self.config.influxdb_rest,self.config.influxdb_database)
            r = requests.post( url, headers=headers, data="\n".join(messurements))
            if r.status_code != 204:
                msg = "Wrong status code {} for query {}".format(r.status_code, url)
                logging.error(msg)
                raise requests.exceptions.ConnectionError(msg)
            return 1
        except requests.exceptions.ConnectionError:
            logging.info("InfluxDB currently not available. Will retry in {} seconds".format(self.config.influxdb_publish_interval))
            return 0
        except Exception as e:
            logging.error("{} got unexpected exception. Will retry in {} seconds".format(e, self.config.influxdb_publish_interval))
            logging.error(traceback.format_exc())
            return -1
