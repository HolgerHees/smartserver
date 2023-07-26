import traceback
import logging
from datetime import datetime, timedelta
import os

import time

from smartserver.confighelper import ConfigHelper

from lib.db import DBException
from lib.helper.forecast import WeatherBlock, WeatherHelper


class ProviderConsumer():
    '''Handler client'''
    def __init__(self, config, mqtt, db, station_consumer ):
        location = config.location.split(",")
        self.latitude = float(location[0])
        self.longitude = float(location[1])

        self.station_consumer = station_consumer

        self.is_running = False

        self.mqtt = mqtt
        self.db = db

        self.dump_path = "{}consumer_provider.json".format(config.lib_path)
        self.version = 1
        self.valid_cache_file = True

        self.current_values = None
        self.forecast_values = None

        self.consume_errors = { "forecast": 0, "current": 0, "summery": 0 }
        self.consume_refreshed = { "forecast": 0, "current": 0, "summery": 0 }

        self.icon_path = config.icon_path

        self.icon_cache = {}

        self.last_consume_error = None

    def start(self):
        self._restore()
        if not os.path.exists(self.dump_path):
            self._dump()

        self.mqtt.subscribe('+/weather/provider/#', self.on_message)

        self.is_running = True

    def terminate(self):
        if self.is_running and os.path.exists(self.dump_path):
            self._dump()
        self.is_running = False

    def _restore(self):
        self.valid_cache_file, data = ConfigHelper.loadConfig(self.dump_path, self.version )
        if data is not None:
            self.consume_refreshed = data["consume_refreshed"]
            logging.info("Loaded consumer (provider) values")

    def _dump(self):
        if self.valid_cache_file:
            ConfigHelper.saveConfig(self.dump_path, self.version, { "consume_refreshed": self.consume_refreshed } )
            logging.info("Saved consumer (provider) values")

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

    def getCachedIcon(self, icon_name):
        if icon_name not in self.icon_cache:
            with open("{}{}".format(self.icon_path, icon_name)) as f:
                self.icon_cache[icon_name] = f.read()
        return self.icon_cache[icon_name]

    def getWidgetSVG(self, last_modified, requested_fields):
        # curl -d 'type=widget' -H "Content-Type: application/x-www-form-urlencoded" -X POST http://172.16.0.201/data/

        result = {}
        if requested_fields is None or "currentCloudsAsSVG" in requested_fields:
            if last_modified < self.consume_refreshed["forecast"]:
                last_modified = self.consume_refreshed["forecast"]
                with self.db.open() as db:
                    data = db.getOffset(0)
                    #logging.info(data)
                    block = WeatherBlock(data['datetime'])
                    block.apply(data)

                    currentRain = self.station_consumer.getValue("rainCurrentInMillimeter")
                    if currentRain > block.getPrecipitationAmountInMillimeter():
                        block.setPrecipitationAmountInMillimeter(currentRain)

                    icon_name = WeatherHelper.convertOctaToSVG(self.latitude, self.longitude, block)
                    result["currentCloudsAsSVG"] = self.getCachedIcon(icon_name)

        return [ result, last_modified ]

    def getDetailOverviewValues(self, last_modified, requested_fields, requested_day = None):
        activeDay = datetime.now() if requested_day is None else datetime.strptime(requested_day, '%Y-%m-%d')
        activeDay = activeDay.replace(hour=0, minute=0, second=0, microsecond=0)

        #isToday = activeDay.strftime('%Y-%m-%d') == datetime.now().strftime('%Y-%m-%d')

        values = {}

        if last_modified < self.consume_refreshed["forecast"]:
            last_modified = self.consume_refreshed["forecast"]
            with self.db.open() as db:
                start = activeDay.replace(hour=0, minute=0, second=0, microsecond=0)
                end = activeDay.replace(hour=23, minute=59, second=59, microsecond=0)

                # DAY VALUES
                if "dayList" in requested_fields:
                    todayValues = [];
                    dayList = db.getRangeList(start, end)

                    minTemperature, maxTemperature, maxWindSpeed, sumSunshine, sumRain = WeatherHelper.calculateSummary(dayList)

                    current_value = WeatherBlock( dayList[0]['datetime'] )

                    index = 0;
                    for hourlyData in dayList:
                        if index > 0 and index % 3 == 0:
                            #_datetime = hourlyData['datetime'].replace(minute=0, second=0);
                            current_value.setEnd(hourlyData['datetime'])
                            icon_name = WeatherHelper.convertOctaToSVG(self.latitude, self.longitude, current_value)
                            current_value.setSVG(self.getCachedIcon(icon_name))
                            todayValues.append( current_value )
                            current_value = WeatherBlock( hourlyData['datetime'] )
                        current_value.apply(hourlyData)
                        index += 1

                    current_value.setEnd(current_value.getStart() + timedelta(hours=3))
                    icon_name = WeatherHelper.convertOctaToSVG(self.latitude, self.longitude, current_value)
                    current_value.setSVG(self.getCachedIcon(icon_name))
                    todayValues.append(current_value)

                    values["dayList"] = todayValues
                    values["dayActive"] = activeDay
                    values["dayMinTemperature"] = minTemperature
                    values["dayMaxTemperature"] = maxTemperature
                    values["dayMaxWindSpeed"] = maxWindSpeed
                    values["daySumSunshine"] = sumSunshine
                    values["daySumRain"] = sumRain

                if requested_day is None and "weekList" in requested_fields:
                    # WEEK VALUES
                    weekValues = []

                    weekFrom = datetime.now().replace(hour=0, minute=0, second=0)
                    weekList = db.getWeekList(weekFrom)

                    minTemperatureWeekly, maxTemperatureWeekly, maxWindSpeedWeekly, sumSunshineWeekly, sumRainWeekly = WeatherHelper.calculateSummary(weekList)

                    start = weekList[0]['datetime'].replace(hour=0, minute=0, second=0)
                    current_value = WeatherBlock( start )
                    index = 1
                    for hourlyData in weekList:
                        _datetime = hourlyData['datetime'].replace(hour=0, minute=0, second=0);
                        if _datetime != current_value.getStart():
                            current_value.setEnd(_datetime)
                            icon_name = WeatherHelper.convertOctaToSVG(self.latitude, self.longitude, current_value)
                            current_value.setSVG(self.getCachedIcon(icon_name))
                            weekValues.append(current_value)
                            current_value = WeatherBlock( _datetime )
                        current_value.apply(hourlyData)
                        index += 1

                    values["weekList"] = weekValues
                    values["weekMinTemperature"] = minTemperatureWeekly
                    values["weekMaxTemperature"] = maxTemperatureWeekly
                    values["weekMaxWindSpeed"] = maxWindSpeedWeekly
                    values["weekSumSunshine"] = sumSunshineWeekly
                    values["weekSumRain"] = sumRainWeekly

                #current_value.setEnd(weekList[-1]['datetime'] + timedelta(hours=24))
                #todayValues.append(current_value)

        return [ values, last_modified ]

    def getTodayOverviewValues(self):
        with self.db.open() as db:
            start = datetime.now()
            if start.hour >= 21:
                start = start.replace(hour=21, minute=0, second=0, microsecond=0)
            elif start.hour >= 16:
                start = start.replace(hour=16, minute=0, second=0, microsecond=0)
            elif start.hour >= 11:
                start = start.replace(hour=11, minute=0, second=0, microsecond=0)
            elif start.hour >= 6:
                start = start.replace(hour=6, minute=0, second=0, microsecond=0)
            elif start.hour >= 1:
                start = start.replace(hour=1, minute=0, second=0, microsecond=0)
            else:
                start = start.replace(hour=21, minute=0, second=0, microsecond=0)

            end = start + timedelta(hours=24)

            dayList = db.getRangeList(start, end)
            todayValues = [];

            blockConfigs = [ 21, 16, 11, 6, 1 ]

            current_value = None;
            for hourlyData in dayList:
                hour = hourlyData['datetime'].hour;

                if hour in blockConfigs:
                    if current_value is not None:
                        current_value.setEnd(hourlyData['datetime'])
                        icon_name = WeatherHelper.convertOctaToSVG(self.latitude, self.longitude, current_value)
                        current_value.setSVG(self.getCachedIcon(icon_name))
                        todayValues.append(current_value)
                    current_value = WeatherBlock( hourlyData['datetime'] )

                current_value.apply(hourlyData)

                if len(todayValues) == 4:
                    break

            minTemperature, maxTemperature, maxWindSpeed, sumSunshine, sumRain = WeatherHelper.calculateSummary(dayList)

            values = {}
            values["dayList"] = todayValues
            values["dayMinTemperature"] = minTemperature
            values["dayMaxTemperature"] = maxTemperature
            values["dayMaxWindSpeed"] = maxWindSpeed
            values["daySumSunshine"] = sumSunshine
            values["daySumRain"] = sumRain

            return values

    def getStateMetrics(self):
        state_metrics = []

        has_errors = False
        for state_name in self.consume_errors:
            if self.consume_errors[state_name] == 0 or self.consume_refreshed[state_name] == 0:
                continue

            if self.consume_refreshed[state_name] - self.consume_errors[state_name] < 300:
                has_errors = True
                break

        state_metrics.append("weather_service_state{{type=\"consumer_provider\"}} {}".format(0 if has_errors else 1))
        return state_metrics
