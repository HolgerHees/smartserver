import traceback
import logging
from datetime import datetime, timedelta
import os
import threading

import time

from smartserver.confighelper import ConfigHelper

from lib.db import DBException
from lib.helper.forecast import WeatherBlock, WeatherHelper


class ProviderConsumer():
    '''Handler client'''
    def __init__(self, config, mqtt, db, station_consumer, handler ):
        location = config.location.split(",")
        self.latitude = float(location[0])
        self.longitude = float(location[1])

        self.handler = handler
        self.station_consumer = station_consumer
        self.station_consumer.registerProviderConsumer(self)

        self.is_running = False

        self.mqtt = mqtt
        self.db = db

        self.dump_path = "{}consumer_provider.json".format(config.lib_path)
        self.version = 1
        self.valid_cache_file = True

        self.processed_current_values = None
        self.processed_forecast_values = None

        self.current_values = None

        self.consume_errors = { "forecast": 0, "current": 0, "summery": 0 }
        self.consume_refreshed = { "forecast": 0, "current": 0, "summery": 0 }

        self.icon_path = config.icon_path

        self.icon_cache = {}

        self.last_consume_error = None

        self.current_is_raining = False

        self.station_fallback_lock = threading.Lock()
        self.station_fallback_data = None
        self.station_cloud_timer = None

        with self.db.open() as db:
            self.field_names = db.getFields()

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
                        #logging.info(datetime_str)
                        #datetime_str = u"{0}{1}".format(datetime_str[:-3],datetime_str[-2:])
                        validFrom = datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M:%S%z')
                        update_values = []
                        for field in self.processed_current_values:
                            self.processed_current_values[field] = float(self.processed_current_values[field]) if "." in self.processed_current_values[field] else int(self.processed_current_values[field])
                            if field in self.field_names:
                                update_values.append("`{}`='{}'".format(field,self.processed_current_values[field]))

                        if db.hasEntry(validFrom.timestamp()):
                            isModified = db.update(validFrom.timestamp(),update_values)
                            logging.info(u"Current data processed • Updated {}".format( "yes" if isModified else "no" ))
                        else:
                            logging.info(u"Current data not updated: Topic: " + msg.topic + ", message:" + str(msg.payload))

                        self.current_values = self.processed_current_values
                        self.processed_current_values = None
                else:
                    if self.processed_current_values is None:
                        self.processed_current_values = {}
                    self.processed_current_values[topic[4]] = msg.payload.decode("utf-8")
            elif state_name == u"forecast":
                if is_refreshed:
                    if self.processed_forecast_values is not None:
                        with self.db.open() as db:
                            updateCount = 0
                            insertCount = 0
                            for datetime_str in self.processed_forecast_values:
                                validFrom = datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M:%S%z')

                                update_values = []
                                for field in self.processed_forecast_values[datetime_str]:
                                    update_values.append(u"`{}`='{}'".format(field,self.processed_forecast_values[datetime_str][field]))

                                isUpdate = db.hasEntry(validFrom.timestamp())
                                try:
                                    isModified = db.insertOrUpdate(validFrom.timestamp(),update_values)
                                    if isModified:
                                        if isUpdate:
                                            updateCount += 1
                                        else:
                                            insertCount += 1
                                except Exception as e:
                                    logging.info(update_values)
                                    raise e
                            logging.info("Forcecasts processed • Total: {}, Updated: {}, Inserted: {}".format(len(self.processed_forecast_values),updateCount,insertCount))

                            self.processed_forecast_values = None
                    else:
                        logging.info("Forcecasts not processed")
                else:
                    if self.processed_forecast_values is None:
                        self.processed_forecast_values = {}
                        
                    field = topic[4]
                    datetime_str = topic[5].replace("plus","+")
                    #datetime_str = u"{0}{1}".format(datetime_str[:-3],datetime_str[-2:])
                    #logging.info("{} {}".format(topic[5], datetime_str))

                    if datetime_str not in self.processed_forecast_values:
                        self.processed_forecast_values[datetime_str] = {}
                        
                    self.processed_forecast_values[datetime_str][field] = msg.payload.decode("utf-8")
            elif state_name == u"summary":
                if is_refreshed:
                    logging.info("Summery data processed")
            else:
                logging.info("Unknown topic " + msg.topic + ", message:" + str(msg.payload))

            if is_refreshed:
                self.consume_refreshed[state_name] = time.time()

                # notify station fallback values
                if state_name == "current":
                    with self.station_fallback_lock:
                        if self.station_fallback_data is not None:
                            for field, value in self._buildFallbackStationValues().items():
                                if field not in self.station_fallback_data or self.station_fallback_data[field] != value:
                                    self.station_fallback_data[field] = value
                                    self.notifyStationValue(field, value)

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

    def _buildFallbackStationValues(self):
        result = {}
        with self.db.open() as db:
            mapping = {
                'currentAirTemperatureInCelsius': "airTemperatureInCelsius",
                'currentPerceivedTemperatureInCelsius': "feelsLikeTemperatureInCelsius",
                'currentWindGustInKilometerPerHour': "maxWindSpeedInKilometerPerHour",
                'currentWindSpeedInKilometerPerHour': "windSpeedInKilometerPerHour",
                'currentRainLastHourInMillimeter': "precipitationAmountInMillimeter",
                'currentUvIndex': "uvIndexWithClouds"
            }
            for field, _field in mapping.items():
                if _field is not None and _field in self.current_values:
                    result[field] = self.current_values[_field]
                else:
                    result[field] = -1

            end = datetime.now()
            start = end.replace(hour=0, minute=0, second=0, microsecond=0)

            values = db.getRangeSum(start, end, ["precipitationAmountInMillimeter"])
            result["currentRainDailyInMillimeter"] = values["precipitationAmountInMillimeter"]

    def _buildCloudSVG(self):
        with self.db.open() as db:
            data = db.getOffset(0)
            if data is not None:
                #logging.info(data)
                block = WeatherBlock(data['datetime'])
                block.apply(data)

                currentRain = 0
                currentRainLevel = self.station_consumer.getValue("rainLevel")
                if currentRainLevel is None:
                    currentRain = data["precipitationAmountInMillimeter"]
                elif currentRainLevel > 0:
                    if self.current_is_raining or currentRainLevel > 2:
                        currentRain = 0.1

                        currentRain15Min = self.station_consumer.getValue("rainLast15MinInMillimeter")
                        if currentRain15Min * 4 > currentRain:
                            currentRain = currentRain15Min * 4

                        currentRain1Hour = self.station_consumer.getValue("rainLastHourInMillimeter")
                        if currentRain1Hour > currentRain:
                            currentRain = currentRain1Hour
                self.current_is_raining = currentRain > 0

                block.setPrecipitationAmountInMillimeter(currentRain)

                cloudCoverInOcta = self.station_consumer.getValue("cloudCoverInOcta")
                if cloudCoverInOcta is None:
                    cloudCoverInOcta = data["effectiveCloudCoverInOcta"]
                block.effectiveCloudCoverInOcta = cloudCoverInOcta
                #logging.info("{}".format(block.effectiveCloudCoverInOcta))

                icon_name = WeatherHelper.convertOctaToSVG(self.latitude, self.longitude, block)

                return self.getCachedIcon(icon_name)
        return None

    def _notifyCloudValue(self):
        self.station_cloud_timer = None
        self.handler.emitChangedCurrentData("currentCloudsAsSVG", self._buildCloudSVG())

    def notifyStationValue(self, field, value):
        with self.station_fallback_lock:
            self.station_fallback_data = None
        self.handler.emitChangedCurrentData(field, value)

        if field in ["currentRainLevel", "currentRainLast15MinInMillimeter", "currentRainLastHourInMillimeter", "currentCloudCoverInOcta"]:
            if self.station_cloud_timer is not None:
                self.station_cloud_timer.cancel()
            self.station_cloud_timer = threading.Timer(15, self._notifyCloudValue)
            self.station_cloud_timer.start()

    def getCurrentValues(self):
        result, _ = self.station_consumer.getValues(-1, None)
        if result is None:
            with self.station_fallback_lock:
                self.station_fallback_data = None

            result = self._buildFallbackStationValues()
        else:
            with self.station_fallback_lock:
                self.station_fallback_data = []

        result["currentCloudsAsSVG"] = self._buildCloudSVG()
        return result


















    def getCurrentValuesOld(self, last_modified, requested_fields = None):
        result, _last_modified = self.station_consumer.getValues(last_modified, requested_fields)

        if result is None:
            with self.station_fallback_lock:
                self.station_fallback_data = None

            if last_modified < self.consume_refreshed["current"]:
                result = self._buildFallbackStationValues()
        else:
            with self.station_fallback_lock:
                self.station_fallback_data = []

        return [result, _last_modified]

    def getWidgetSVGOld(self, last_modified, requested_fields):
        # curl -d 'type=widget' -H "Content-Type: application/x-www-form-urlencoded" -X POST http://172.16.0.201/data/

        result = {}
        if requested_fields is None or "currentCloudsAsSVG" in requested_fields:
            _station_last_modified = self.station_consumer.getLastModified(last_modified, ["rainLevel", "rainLast15MinInMillimeter", "rainLastHourInMillimeter", "cloudCoverInOcta"])

            if last_modified < self.consume_refreshed["forecast"] or last_modified < _station_last_modified:
                if _station_last_modified > last_modified:
                    last_modified = _station_last_modified
                if self.consume_refreshed["forecast"] > last_modified:
                    last_modified = self.consume_refreshed["forecast"]

                currentCloudsAsSVG = self._buildCloudSVG()
                if currentCloudsAsSVG is not None:
                    result["currentCloudsAsSVG"] = currentCloudsAsSVG

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
                    if len(dayList) > 0:
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

                    else:
                        minTemperature = maxTemperature = maxWindSpeed = sumSunshine = sumRain = activeDay = None

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
                    if len(weekList) > 0:
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
                    else:
                        minTemperatureWeekly = maxTemperatureWeekly = maxWindSpeedWeekly = sumSunshineWeekly = sumRainWeekly = None

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
            values = {}
            if len(dayList) > 0:
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
            else:
                minTemperature = maxTemperature = maxWindSpeed = sumSunshine = sumRain = None

            values["dayList"] = todayValues
            values["dayMinTemperature"] = minTemperature
            values["dayMaxTemperature"] = maxTemperature
            values["dayMaxWindSpeed"] = maxWindSpeed
            values["daySumSunshine"] = sumSunshine
            values["daySumRain"] = sumRain

            return values

    def getStateMetrics(self):
        now = time.time()
        has_any_update = False
        has_errors = False
        for state_name in self.consume_errors:
            if now - self.consume_refreshed[state_name] < 60 * 60 * 2:
                has_any_update = True

            if self.consume_errors[state_name] != 0 and self.consume_refreshed[state_name] != 0:
                if self.consume_refreshed[state_name] - self.consume_errors[state_name] < 300:
                    has_errors = True

        state_metrics = []
        state_metrics.append("weather_service_state{{type=\"consumer_provider\",group=\"data\"}} {}".format(1 if has_any_update else 0))
        state_metrics.append("weather_service_state{{type=\"consumer_provider\",group=\"running\"}} {}".format(1 if self.is_running and not has_errors else 0))
        return state_metrics
