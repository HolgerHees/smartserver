import os
import logging
import traceback
import time

from smartserver.confighelper import ConfigHelper


class StationConsumer():
    '''Handler client'''
    def __init__(self, config, mqtt):
        self.mqtt = mqtt

        self.is_running = False

        self.dump_path = "{}consumer_station.json".format(config.lib_path)
        self.version = 1
        self.valid_cache_file = True

        self.station_values = {}

        self.last_consume_error = None

    def start(self):
        self._restore()
        if not os.path.exists(self.dump_path):
            self._dump()
        self.mqtt.subscribe('+/weather/station/#', self.on_message)
        self.is_running = True

    def terminate(self):
        if self.is_running and os.path.exists(self.dump_path):
            self._dump()
        self.is_running = False

    def _restore(self):
        self.valid_cache_file, data = ConfigHelper.loadConfig(self.dump_path, self.version )
        if data is not None:
            self.station_values = data["station_values"]
            logging.info("Loaded {} consumer (station) values".format(len(self.station_values)))

    def _dump(self):
        if self.valid_cache_file:
            ConfigHelper.saveConfig(self.dump_path, self.version, { "station_values": self.station_values } )
            logging.info("Saved {} consumer (station) values".format(len(self.station_values)))

    def on_message(self,client,userdata,msg):
        topic = msg.topic.split("/")

        #logging.info(topic)

        #logging.info("Station: {} => {}".format(topic[3], msg.payload.decode("utf-8")))

        value = msg.payload.decode("utf-8")
        value = float(value) if "." in value else int(value)
        self.station_values[ topic[3] ] = { "time": time.time(), "value": value  }

    def getValue(self, key, fallback = None ):
        return self.station_values[key]["value"] if key in self.station_values else fallback

    def getValues(self, last_modified, requested_fields = None ):
        _last_modified = last_modified
        if len(self.station_values) > 0:
            result = {}
            for key, data in self.station_values.items():
                key = "current{}{}".format(key[0].upper(),key[1:])
                if requested_fields is not None and key not in requested_fields:
                    continue
                if last_modified < data["time"]:
                    result[key] = data["value"]
                    if _last_modified < data["time"]:
                        _last_modified = data["time"]
        else:
            result = None
        return [result, _last_modified]

    def getLastModified(self, last_modified, requested_fields = None ):
        _last_modified = last_modified
        for key, data in self.station_values.items():
            if requested_fields is not None and key not in requested_fields:
                continue
            if last_modified < data["time"] and _last_modified < data["time"]:
                _last_modified = data["time"]
        return _last_modified

    def getStateMetrics(self):
        has_any_update = False
        now = time.time()
        for key, item in self.station_values.items():
            if now - item["time"] < 60 * 60 * 2:
                has_any_update = True
                break

        state_metrics = []
        state_metrics.append("weather_service_state{{type=\"consumer_station\",group=\"data\"}} {}".format(1 if has_any_update else 0))
        state_metrics.append("weather_service_state{{type=\"consumer_station\",group=\"running\"}} {}".format(1 if self.is_running else 0))
        return state_metrics
