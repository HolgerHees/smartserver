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

      self.is_running = False
      self.event = threading.Event()

      self.config = config

      self.callbacks = []

      self.state_metrics = -1

    def getStateMetrics(self):
        return ["system_service_state{{type=\"influxdb\"}} {}".format(self.state_metrics)]

    def start(self):
        self.is_running = True
        super().start()

    def terminate(self):
        #logging.info("Shutdown influxdb")

        self.is_running = False
        self.event.set()

    def run(self):
        logging.info("Influxdb started")
        while self.is_running:
            messurements = []
            try:
                for callback in self.callbacks:
                    messurements += callback()
                self.state_metrics = self.submit(messurements)
            except Exception as e:
                logging.error("Got unexpected exception. Will retry in {} seconds".format(self.config.influxdb_publish_interval))
                logging.error(traceback.format_exc())
                self.state_metrics = -1

            self.event.wait(self.config.influxdb_publish_interval)

        logging.info("Influxdb stopped")

    def register(self, callback):
        self.callbacks.append(callback)

    #def get(self, messurements):
    #    #curl -G 'http://localhost:8086/query?pretty=true' --data-urlencode "db=mydb" --data-urlencode "q=SELECT \"value\" FROM \"cpu_load_short\" WHERE \"region\"='us-west';SELECT count(\"value\") FROM \"cpu_load_short\" WHERE \"region\"='us-west'"

    #    queries = []
    #    for messurement in messurements:
    #        queries.append("SELECT last(\"value\") FROM \"{}\"".format(messurement))

    #    results = self.query(queries)
    #    values = {}
    #    if results is not None:
    #        for result in results:
    #            if result is None or len(result["values"]) < 1:
    #                continue
    #            values[result["name"]] = result["values"][1]
    #    return values

    def query(self, query):
        headers = {'Authorization': "Token {}".format(self.config.influxdb_token), "Content-Type": "application/vnd.influxql"}
        url = "{}/query?pretty=true&db={}&rp=autogen&q={}".format(self.config.influxdb_rest,self.config.influxdb_database, urllib.parse.quote(";".join([query])))

        r = requests.get( url, headers=headers)

        if r.status_code != 200:
            logging.info("Wrong status code {} for query {}".format(r.status_code, url))
            return None

        try:
            data = json.loads(r.text)
            #logging.info(data)
            if len(data["results"]) == 1:
                if "series" in data["results"][0] and len(data["results"][0]["series"]) > 0:
                    return data["results"][0]["series"]
            return []

        except Exception as e:
            logging.error("Got unexpected exception")
            logging.error(traceback.format_exc())
            return None

    def submit(self, messurements):
        return self._submit(messurements, self.config.influxdb_database)

    def _submit(self, messurements, db):
        try:
            if len(messurements) == 0:
                return 1

            logging.info("Submit {} messurements".format(len(messurements)))

            headers = {'Authorization': "Token {}".format(self.config.influxdb_token), 'Content-type': 'application/json; charset=utf-8' }
            url = "{}/write?db={}&rp=autogen&precision=ms&consistency=one".format(self.config.influxdb_rest,db)
            r = requests.post( url, headers=headers, data="\n".join(messurements).encode("utf-8") )
            if r.status_code != 204:
                msg = "Wrong status code {} for query {}".format(r.status_code, url)
                logging.error(msg)
                if r.content != "":
                    logging.error("BODY: {}".format(r.content))
                raise requests.exceptions.ConnectionError(msg)
            return 1
        except requests.exceptions.ConnectionError:
            logging.info("InfluxDB currently not available. Will retry in {} seconds".format(self.config.influxdb_publish_interval))
            return 0
        except Exception as e:
            logging.error("Got unexpected exception. Will retry in {} seconds".format(self.config.influxdb_publish_interval))
            logging.error(traceback.format_exc())
            return -1

    @staticmethod
    def escapeValue(value):
        return value.replace(" ","\\ ").replace(",","\\,")
