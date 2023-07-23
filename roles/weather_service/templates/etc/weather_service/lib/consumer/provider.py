import traceback
import logging
from datetime import datetime

import time

from lib.db import DBException
from lib.helper.forecast import WeatherBlock, WeatherHelper


class ProviderConsumer():
    '''Handler client'''
    def __init__(self, config, mqtt, db):
        location = config.location.split(",")
        self.latitude = float(location[0])
        self.longitude = float(location[1])

        self.mqtt = mqtt
        self.db = db

        self.current_values = None
        self.forecast_values = None

        self.consume_errors = { "forecast": 0, "current": 0, "summery": 0 }
        self.consume_refreshed = { "forecast": 0, "current": 0, "summery": 0 }

        self.icon_path = config.icon_path

        self.icon_cache = {}

        self.last_consume_error = None

    def start(self):
        self.mqtt.subscribe('+/weather/provider/#', self.on_message)

    def terminate(self):
        pass

    def on_message(self,client,userdata,msg):
        topic = msg.topic.split("/")
        if topic[3] == u"current":
            state_name = "current"
        elif topic[3] == u"forecast":
            state_name = "forecast"
        if topic[3] == u"items":
            state_name = "summary"

        is_refreshed = topic[4] == u"refreshed"

        try:
            #logging.info("Topic " + msg.topic + ", message:" + str(msg.payload))
            if state_name == u"current":
                if is_refreshed:
                    with self.db.open() as db:
                        datetime_str = msg.payload.decode("utf-8")
                        datetime_str = u"{0}{1}".format(datetime_str[:-3],datetime_str[-2:])
                        validFrom = datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M:%S%z')

                        update_values = []
                        for field in self.current_values:
                            update_values.append("`{}`='{}'".format(field,self.current_values[field]))

                        if db.hasEntry(validFrom.timestamp()):
                            isModified = db.update(validFrom.timestamp(),update_values)
                            logging.info(u"Current data processed • Updated {}".format( "yes" if isModified else "no" ))
                        else:
                            logging.info(u"Current data not updated: Topic: " + msg.topic + ", message:" + str(msg.payload))

                        self.current_values = None
                else:
                    if self.current_values is None:
                        self.current_values = {}
                    self.current_values[topic[4]] = msg.payload.decode("utf-8")
            elif state_name == u"forecast":
                if is_refreshed:
                    if self.forecast_values is not None:
                        with self.db.open() as db:
                            updateCount = 0
                            insertCount = 0
                            for datetime_str in self.forecast_values:
                                validFrom = datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M:%S%z')

                                update_values = []
                                for field in self.forecast_values[datetime_str]:
                                    update_values.append(u"`{}`='{}'".format(field,self.forecast_values[datetime_str][field]))

                                isUpdate = db.hasEntry(validFrom.timestamp())
                                isModified = db.insertOrUpdate(validFrom.timestamp(),update_values)
                                if isModified:
                                    if isUpdate:
                                        updateCount += 1
                                    else:
                                        insertCount += 1

                            logging.info("Forcecasts processed • Total: {}, Updated: {}, Inserted: {}".format(len(self.forecast_values),updateCount,insertCount))

                            self.forecast_values = None
                    else:
                        logging.info("Forcecasts not processed")
                else:
                    if self.forecast_values is None:
                        self.forecast_values = {}
                        
                    field = topic[4]
                    datetime_str = topic[5].replace("plus","+")
                    datetime_str = u"{0}{1}".format(datetime_str[:-3],datetime_str[-2:])
                    
                    if datetime_str not in self.forecast_values:
                        self.forecast_values[datetime_str] = {}
                        
                    self.forecast_values[datetime_str][field] = msg.payload.decode("utf-8")
            elif state_name == u"summary":
                if is_refreshed:
                    logging.info("Summery data processed")
            else:
                logging.info("Unknown topic " + msg.topic + ", message:" + str(msg.payload))

            if is_refreshed:
                self.consume_refreshed[state_name] = time.time()
        except DBException:
            self.consume_errors[state_name] = time.time()
        #except MySQLdb._exceptions.OperationalError as e:
        #    logging.info("{}: {}".format(str(e.__class__),str(e)))
        #    self.service_metrics["mysql"] = 0
        #    self.consume_errors[state_name] = time.time()
        except Exception as e:
            logging.info("{}: {}".format(str(e.__class__),str(e)))
            traceback.print_exc()
            self.consume_errors[state_name] = time.time()

    def resetIconCache(self):
        self.icon_cache = {}

    def getWidgetSVG(self, last_modified, requested_fields = None):
        # curl -d 'type=widget' -H "Content-Type: application/x-www-form-urlencoded" -X POST http://172.16.0.201/data/
        _last_modified = datetime.now().replace(minute=0, second=0, microsecond=0).timestamp()
        if self.consume_refreshed["forecast"] > _last_modified:
            _last_modified = self.consume_refreshed["forecast"]

        result = {}
        if requested_fields is None or "currentCloudsAsSVG" in requested_fields:
            if last_modified < _last_modified:
                with self.db.open() as db:
                    data = db.getOffset(0)
                    #logging.info(data)
                    block = WeatherBlock(data['datetime'])
                    block.apply(data)

                    icon_name = WeatherHelper.convertOctaToSVG(self.latitude, self.longitude, block)
                    if icon_name not in self.icon_cache:
                        with open("{}{}".format(self.icon_path, icon_name)) as f:
                            self.icon_cache[icon_name] = f.read()

                    result["currentCloudsAsSVG"] = self.icon_cache[icon_name]

        return [ result, _last_modified ]

    def getWidgetValues(self, last_modified):
        # curl -d 'type=widget' -H "Content-Type: application/x-www-form-urlencoded" -X POST http://172.16.0.201/data/

        result = {}
        if last_modified < self.consume_refreshed["forecast"]:
            with self.db.open() as db:
                data = db.getOffset(0)
                #logging.info(data)
                block = WeatherBlock(data['datetime'])
                block.apply(data)

                icon_name = WeatherHelper.convertOctaToSVG(self.latitude, self.longitude, block)
                with open("{}{}".format(self.icon_path, icon_name)) as f:
                    result["currentCloudsAsSVG"] = f.read()
        return [ result, self.consume_refreshed["forecast"] ]

    def getStateMetrics(self):
        state_metrics = []

        has_errors = False
        for state_name in self.consume_errors:
            if self.consume_errors[state_name] is None or self.consume_refreshed[state_name] is None:
                continue

            if self.consume_refreshed[state_name] - self.consume_errors[state_name] < 300:
                has_errors = True
                break

        state_metrics.append("weather_service_state{{type=\"consumer_provider\"}} {}".format(0 if has_errors else 1))
        return state_metrics
