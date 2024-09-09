import threading
import logging
import schedule
import time
import requests
import traceback
from datetime import datetime, timedelta
import os

from smartserver.confighelper import ConfigHelper

from lib.db import DBException


summeryOffsets = [0,4,8]
summeryFields = ["airTemperatureInCelsius","effectiveCloudCoverInOcta"]

class AuthException(Exception):
    pass

class RequestDataException(Exception):
    pass

class CurrentDataException(RequestDataException):
    pass

class ForecastDataException(RequestDataException):
    pass

class Provider:
    def __init__(self, config, db, mqtt, dump_path):
        self.is_running = False
        self.is_fetching = False

        self.config = config
        self.db = db
        self.mqtt = mqtt

        self.service_metrics = { "data_provider": -1, "data_current": -1, "data_forecast": -1, "publish": -1 }

        self.dump_path = dump_path
        self.version = 1
        self.valid_cache_file = True

        self.last_fetch = 0

    def start(self):
        self._restore()
        if not os.path.exists(self.dump_path):
            self._dump()

        self.is_running = True

        schedule.every().hour.at("05:00").do(self.fetchInterval)
        if time.time() - self.last_fetch > 60 * 60:
            schedule.every().second.do(self.fetchOneTime)

    def terminate(self):
        if self.is_running and os.path.exists(self.dump_path):
            self._dump()
        self.is_running = False

    def _restore(self):
        self.valid_cache_file, data = ConfigHelper.loadConfig(self.dump_path, self.version )
        if data is not None:
            self.last_fetch = data["last_fetch"]
            logging.info("Loaded provider state")

    def _dump(self):
        if self.valid_cache_file:
            ConfigHelper.saveConfig(self.dump_path, self.version, { "last_fetch": self.last_fetch } )
            logging.info("Saved provider state")

    def _createFetcher(self, config):
        raise NotImplementedError()

    def triggerSummerizedItems(self, db, mqtt):
        with db.open() as db:
            result = db.getFullDay()

            if len(result) > 0:
                tmp = {}
                for field in summeryFields:
                    tmp[field] = [ None, None, 0.0 ]
                for row in result:
                    for field in tmp:
                        value = row[field]
                        if tmp[field][0] == None:
                            tmp[field][0] = value
                            tmp[field][1] = value
                        else:
                            if tmp[field][0] > value:
                                tmp[field][0] = value
                            if tmp[field][1] < value:
                                tmp[field][1] = value
                        tmp[field][2] = tmp[field][2] + value

                for field in summeryFields:
                    tmp[field][2] = tmp[field][2] / len(result)

                    mqtt.publish("{}/weather/provider/items/{}/{}".format(self.config.publish_provider_topic,field,"min"), payload=str(tmp[field][0]).encode("utf-8"), qos=0, retain=False)
                    mqtt.publish("{}/weather/provider/items/{}/{}".format(self.config.publish_provider_topic,field,"max"), payload=str(tmp[field][1]).encode("utf-8"), qos=0, retain=False)
                    mqtt.publish("{}/weather/provider/items/{}/{}".format(self.config.publish_provider_topic,field,"avg"), payload=str(tmp[field][2]).encode("utf-8"), qos=0, retain=False)

                for offset in summeryOffsets:
                    data = db.getOffset(offset)
                    for field, value in data.items():
                        mqtt.publish("{}/weather/provider/items/{}/{}".format(self.config.publish_provider_topic,field,offset), payload=str(value).encode("utf-8"), qos=0, retain=False)
                mqtt.publish("{}/weather/provider/items/refreshed".format(self.config.publish_provider_topic), payload="1", qos=0, retain=False)

                logging.info("Summery data published")
            else:
                logging.info("Summery data skipped. Not enough data.")

    def fetchOneTime(self):
        self.is_fetching = True
        self.fetch()
        self.is_fetching = False

        return schedule.CancelJob

    def fetchInterval(self, repeat_count = 0):
        if repeat_count == 0:
            if self.is_fetching:
                logging.warn("Skip fetching. Older job is still runing")
                return
            self.is_fetching = True

        if not self.fetch() and self.is_running:
            _repeat_count = repeat_count + 1
            sleepTime = 600 * _repeat_count if _repeat_count < 6 else 3600
            logging.info("Sleep {} seconds".format(sleepTime))
            schedule.every(sleepTime).seconds.do(self.fetchInterval, repeat_count=_repeat_count)
        else:
            self.is_fetching = False

        if repeat_count > 0:
            return schedule.CancelJob

    def fetch(self):
        try:
            fetcher = self._createFetcher(self.config)

            if not self.is_running:
                return False

            fetcher.fetchForecast(self.mqtt)
            self.service_metrics["data_forecast"] = 1

            if not self.is_running:
                return False

            fetcher.fetchCurrent(self.db, self.mqtt)
            self.service_metrics["data_current"] = 1

            if not self.is_running:
                return False

            self.triggerSummerizedItems(self.db, self.mqtt)

            date = datetime.now()
            target = date.replace(minute=5,second=0)
            if target <= date:
                target = target + timedelta(hours=1)
            diff = target - date

            self.service_metrics["data_provider"] = 1
            self.service_metrics["publish"] = 1

            self.last_fetch = time.time()

            return True
        except ForecastDataException as e:
            logging.info("{}: {}".format(str(e.__class__),str(e)))
            self.service_metrics["data_forecast"] = 0
        except CurrentDataException as e:
            logging.info("{}: {}".format(str(e.__class__),str(e)))
            self.service_metrics["data_current"] = 0
        except (RequestDataException,AuthException,requests.exceptions.RequestException) as e:
            logging.info("{}: {}".format(str(e.__class__),str(e)))
            self.service_metrics["data_provider"] = 0
        except DBException:
            pass
        #except MQTT Exceptions?? as e:
        #    logging.info("{}: {}".format(str(e.__class__),str(e)))
        #    self.service_metrics["mqtt"] = 0
        #    error_count += 1
        except Exception as e:
            logging.info("{}: {}".format(str(e.__class__),str(e)))
            traceback.print_exc()
            self.service_metrics["publish"] = 0

        return False

    def getStateMetrics(self):
        state_metrics = []
        for name, value in self.service_metrics.items():
            state_metrics.append("weather_service_state{{type=\"provider\", group=\"{}\"}} {}".format(name,value))

        max_hours = 3 if self.is_fetching else 6
        state = 1 if time.time() - self.last_fetch < 60 * 60 * max_hours else 0

        state_metrics.append("weather_service_state{{type=\"provider\", group=\"running\"}} {}".format(state))
        return state_metrics
