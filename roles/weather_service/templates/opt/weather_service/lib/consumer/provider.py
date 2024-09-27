import traceback
import logging
from datetime import datetime, timedelta
import os
import threading
import schedule

import time

from smartserver.confighelper import ConfigHelper
from smartserver.metric import Metric

from lib.db import DBException
from lib.helper.forecast import WeatherBlock, WeatherHelper


class ProviderConsumer():
    '''Handler client'''
    def __init__(self, config, mqtt, db, handler ):
        location = config.location.split(",")
        self.latitude = float(location[0])
        self.longitude = float(location[1])

        self.handler = handler

        self.is_running = False

        self.mqtt = mqtt
        self.db = db

        self.dump_path = "{}consumer_provider.json".format(config.lib_path)
        self.version = 1
        self.valid_cache_file = True

        self.processed_current_values = None
        self.processed_forecast_values = None

        self.consume_errors = { "forecast": 0, "current": 0, "summery": 0 }
        self.consume_refreshed = { "forecast": 0, "current": 0, "summery": 0 }

        self.icon_path = config.icon_path

        self.icon_cache = {}

        self.last_consume_error = None

        self.current_is_raining = False

        self.station_fallback_lock = threading.Lock()
        self.station_fallback_data = None
        self.station_cloud_timer = None
        self.station_cloud_svg = None

        self.station_values = {}
        self.station_values_last_modified = 0

        self.is_night = False;

        with self.db.open() as db:
            self.field_names = db.getFields()
            self.current_values = db.getOffset(0)

    def start(self):
        self._restore()
        if not os.path.exists(self.dump_path):
            self._dump()

        self.mqtt.subscribe('+/weather/provider/#', self.on_message)

        self.checkSunriseSunset()
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
                    if self.processed_current_values is not None:
                        currentIsModified = False
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
                                currentIsModified = db.update(validFrom.timestamp(),update_values)
                                self.current_values = db.getOffset(0)
                                logging.info(u"Current data processed • Updated {}".format( "yes" if currentIsModified else "no" ))
                            else:
                                logging.info(u"Current data not updated: Topic: " + msg.topic + ", message:" + str(msg.payload))

                        self.processed_current_values = None
                        if currentIsModified:
                            with self.station_fallback_lock:
                                if self.station_fallback_data is not None:
                                    for field, value in self._buildFallbackStationValues().items():
                                        if field in self.station_fallback_data and self.station_fallback_data[field] == value:
                                            continue
                                        self.station_fallback_data[field] = value
                                        self.notifyCurrentValue(field, value)
                    else:
                        logging.info("Current not processed")
                else:
                    if self.processed_current_values is None:
                        self.processed_current_values = {}
                    self.processed_current_values[topic[4]] = msg.payload.decode("utf-8")
            elif state_name == u"forecast":
                if is_refreshed:
                    if self.processed_forecast_values is not None:
                        forecastsIsModified = False
                        updateCount = 0
                        insertCount = 0
                        with self.db.open() as db:
                            for datetime_str in self.processed_forecast_values:
                                validFrom = datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M:%S%z')

                                update_values = []
                                for field in self.processed_forecast_values[datetime_str]:
                                    update_values.append(u"`{}`='{}'".format(field,self.processed_forecast_values[datetime_str][field]))

                                isUpdate = db.hasEntry(validFrom.timestamp())
                                try:
                                    isModified = db.insertOrUpdate(validFrom.timestamp(),update_values)
                                    if isModified:
                                        forecastsIsModified = True
                                        if isUpdate:
                                            updateCount += 1
                                        else:
                                            insertCount += 1
                                except Exception as e:
                                    logging.info(update_values)
                                    raise e

                        logging.info("Forcecasts processed • Total: {}, Updated: {}, Inserted: {}".format(len(self.processed_forecast_values),updateCount,insertCount))
                        self.processed_forecast_values = None
                        if forecastsIsModified:
                            self.handler.notifyChangedWeekData()
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

        except DBException:
            self.consume_errors[state_name] = time.time()
        #except MySQLdb._exceptions.OperationalError as e:
        #    logging.info("{}: {}".format(str(e.__class__),str(e)))
        #    self.service_metrics["mariadb"] = 0
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

    def stationValuesOutdated(self):
        return time.time() - self.station_values_last_modified > 60 * 60 * 1

    def _buildFallbackStationValues(self):
        result = {}
        mapping = {
            'currentAirTemperatureInCelsius': "airTemperatureInCelsius",
            'currentPerceivedTemperatureInCelsius': "feelsLikeTemperatureInCelsius",
            'currentWindGustInKilometerPerHour': "maxWindSpeedInKilometerPerHour",
            'currentWindSpeedInKilometerPerHour': "windSpeedInKilometerPerHour",
            'currentRainLastHourInMillimeter': "precipitationAmountInMillimeter",
            'currentUvIndex': "uvIndexWithClouds"
        }

        if self.current_values is None:
            for field, _field in mapping.items():
                result[field] = -1
        else:
            for field, _field in mapping.items():
                if _field is not None and _field in self.current_values:
                    result[field] = self.current_values[_field]
                else:
                    result[field] = -1

            end = datetime.now()
            start = end.replace(hour=0, minute=0, second=0, microsecond=0)

            result["currentRainLast15MinInMillimeter"] = 0
            result["currentRainLastHourInMillimeter"] = 0
            result["currentRainLevel"] = 0

            with self.db.open() as db:
                values = db.getRangeSum(start, end, ["precipitationAmountInMillimeter"])
            result["currentRainDailyInMillimeter"] = values["precipitationAmountInMillimeter"]


        return result

    def _buildCloudSVG(self):
        if self.current_values is None:
            return None

        block = WeatherBlock(datetime.now())
        block.apply(self.current_values)

        currentRain = 0
        currentRainLevel = self.station_values["currentRainLevel"] if not self.stationValuesOutdated() else None
        if currentRainLevel is None:
            currentRain = self.current_values["precipitationAmountInMillimeter"]
        elif currentRainLevel > 0:
            if self.current_is_raining or currentRainLevel > 2:
                currentRain = 0.1
                currentRain15Min = self.station_values["currentRainLast15MinInMillimeter"]
                if currentRain15Min * 4 > currentRain:
                    currentRain = currentRain15Min * 4

                currentRain1Hour = self.station_values["currentRainLastHourInMillimeter"]
                if currentRain1Hour > currentRain:
                    currentRain = currentRain1Hour
        self.current_is_raining = currentRain > 0

        block.setPrecipitationAmountInMillimeter(currentRain)

        cloudCoverInOcta = self.station_values["currentCloudCoverInOcta"] if not self.stationValuesOutdated() else None
        if cloudCoverInOcta is None:
            cloudCoverInOcta = self.current_values["effectiveCloudCoverInOcta"]
        block.effectiveCloudCoverInOcta = cloudCoverInOcta
        #logging.info("{}".format(block.effectiveCloudCoverInOcta))

        icon_name = WeatherHelper.convertOctaToSVG(self.latitude, self.longitude, block)

        return self.getCachedIcon(icon_name)

    def notifyStationValue(self, is_update, field, value, time):
        self.station_values[field] = value;
        if time > self.station_values_last_modified:
            self.station_values_last_modified = time

        if is_update:
            with self.station_fallback_lock:
                self.station_fallback_data = None
            self.notifyCurrentValue(field, value)

    def notifyCurrentValue(self, field, value):
        self.handler.notifyChangedCurrentData(field, value)

        if field in ["currentRainLevel", "currentRainLast15MinInMillimeter", "currentRainLastHourInMillimeter", "currentCloudCoverInOcta"]:
            if self.station_cloud_timer is not None:
                self.station_cloud_timer.cancel()
            self.station_cloud_timer = threading.Timer(15, self._notifyCloudValue)
            self.station_cloud_timer.start()

    def checkSunriseSunset(self):
        sunrise, sunset = WeatherHelper.getSunriseAndSunset(self.latitude, self.longitude)
        now = datetime.now()
        is_night = ( now <= sunrise or now >= sunset )
        if is_night != self.is_night:
            self.is_night = is_night
            self._notifyCloudValue()

        logging.info("TRIGGER: checkSunriseSunset => " + str(self.is_night))

        if now < sunrise or now > sunset:
            logging.info("SCHEDULE SUNRISE: " + sunrise.strftime("%H:%M:%S"))
            schedule.every().day.at(sunrise.strftime("%H:%M:%S")).do(self.checkSunriseSunset)
        else:
            logging.info("SCHEDULE SUNSET: " + sunset.strftime("%H:%M:%S"))
            schedule.every().day.at(sunset.strftime("%H:%M:%S")).do(self.checkSunriseSunset)

        return schedule.CancelJob

    def _notifyCloudValue(self):
        self.station_cloud_timer = None
        currentCloudsAsSVG = self._buildCloudSVG()
        if self.station_cloud_svg != currentCloudsAsSVG:
            self.handler.notifyChangedCurrentData("currentCloudsAsSVG", currentCloudsAsSVG)
            self.station_cloud_svg = currentCloudsAsSVG

    def getCurrentValues(self):
        result = {}
        if not self.stationValuesOutdated():
            result = self.station_values
            with self.station_fallback_lock:
                self.station_fallback_data = None
        else:
            with self.station_fallback_lock:
                self.station_fallback_data = self._buildFallbackStationValues()
            result = self.station_fallback_data

        if self.station_cloud_svg is None:
            self.station_cloud_svg = self._buildCloudSVG()

        result["currentCloudsAsSVG"] = self.station_cloud_svg

        is_raining = result["currentRainLast15MinInMillimeter"] > 0 or result["currentRainLastHourInMillimeter"] > 0 or result["currentRainLevel"] > 0
        result["currentRainProbabilityInPercent"] = 0 if self.current_values is None or not is_raining else self.current_values["precipitationProbabilityInPercent"]
        result["currentSunshineDurationInMinutes"] = 0 if self.current_values is None else self.current_values["sunshineDurationInMinutes"]
        return result

    def _convertToDictList(self, blockList):
        result = []
        for block in blockList:
            result.append(block.to_dict())
        return result

    def _applyWeekDay(self, current_value, weekValues):
        current_value.setEnd((current_value.getStart() + timedelta(hours=24)).replace(hour=0, minute=0, second=0))
        icon_name = WeatherHelper.convertOctaToSVG(self.latitude, self.longitude, current_value)
        current_value.setSVG(self.getCachedIcon(icon_name))
        weekValues.append(current_value)

    def getWeekValues(self, requested_day = None):
        activeDay = datetime.now() if requested_day is None else datetime.strptime(requested_day, '%Y-%m-%d')
        activeDay = activeDay.replace(hour=0, minute=0, second=0, microsecond=0)

        values = {}

        with self.db.open() as db:
            start = activeDay.replace(hour=0, minute=0, second=0, microsecond=0)
            end = activeDay.replace(hour=23, minute=59, second=59, microsecond=0)

            # DAY VALUES
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

            values["dayList"] = self._convertToDictList(todayValues)
            values["dayActive"] = activeDay.isoformat()
            values["dayMinTemperature"] = minTemperature
            values["dayMaxTemperature"] = maxTemperature
            values["dayMaxWindSpeed"] = maxWindSpeed
            values["daySumSunshine"] = sumSunshine
            values["daySumRain"] = sumRain

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
                        self._applyWeekDay(current_value, weekValues)
                        current_value = WeatherBlock( _datetime )
                    current_value.apply(hourlyData)
                    index += 1

                self._applyWeekDay(current_value, weekValues)
            else:
                minTemperatureWeekly = maxTemperatureWeekly = maxWindSpeedWeekly = sumSunshineWeekly = sumRainWeekly = None

            values["weekList"] = self._convertToDictList(weekValues)
            values["weekMinTemperature"] = minTemperatureWeekly
            values["weekMaxTemperature"] = maxTemperatureWeekly
            values["weekMaxWindSpeed"] = maxWindSpeedWeekly
            values["weekSumSunshine"] = sumSunshineWeekly
            values["weekSumRain"] = sumRainWeekly

        return values

    def getTodayOverviewValues(self):
        with self.db.open() as db:
            start = datetime.now()
            start = start.replace(minute=0, second=0, microsecond=0)
            end = start + timedelta(hours=24)

            dayList = db.getRangeList(start, end)
            values = {}
            if len(dayList) > 0:
                todayValues = [];

                blockConfigs = []

                current_value = None;
                hour_count = 0
                for hourlyData in dayList:
                    hour = hourlyData['datetime'].hour;
                    if hour_count >= 5:
                        current_value.setEnd(hourlyData['datetime'])
                        icon_name = WeatherHelper.convertOctaToSVG(self.latitude, self.longitude, current_value)
                        current_value.setSVG(self.getCachedIcon(icon_name))
                        todayValues.append(current_value)
                        current_value = None
                        hour_count = 0

                    if current_value is None:
                        current_value = WeatherBlock( hourlyData['datetime'] )

                    current_value.apply(hourlyData)
                    if len(todayValues) == 4:
                        break

                    hour_count += 1

                minTemperature, maxTemperature, maxWindSpeed, sumSunshine, sumRain = WeatherHelper.calculateSummary(dayList)
            else:
                minTemperature = maxTemperature = maxWindSpeed = sumSunshine = sumRain = None

            values["dayList"] = self._convertToDictList(todayValues)
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

        return [
            Metric.buildProcessMetric("weather_service", "consumer_provider", "1" if self.is_running and not has_errors else "0"),
            Metric.buildStateMetric("weather_service", "consumer_provider", "cache_file", "1" if self.valid_cache_file else "0"),
            Metric.buildStateMetric("weather_service", "consumer_provider", "not_outdatet", "1" if has_any_update else "0")
        ]
