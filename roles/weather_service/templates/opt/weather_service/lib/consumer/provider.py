import traceback
import logging
from datetime import datetime, timedelta
import os
import threading
import schedule

import time
import urllib.parse

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
        self.version = 2
        self.valid_cache_file = True

        self.processed_values = {}

        self.last_error = 0
        self.last_refreshed = 0

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

        self.mqtt.subscribe('+/weather/provider/forecast/#', self.on_message)

        self.checkSunriseSunset()
        self.is_running = True

    def terminate(self):
        if self.is_running and os.path.exists(self.dump_path):
            self._dump()
        self.is_running = False

    def _restore(self):
        self.valid_cache_file, data = ConfigHelper.loadConfig(self.dump_path, self.version )
        if data is not None:
            self.last_refreshed = data["last_refreshed"]
            logging.info("Loaded consumer (provider) values")

    def _dump(self):
        if self.valid_cache_file:
            ConfigHelper.saveConfig(self.dump_path, self.version, { "last_refreshed": self.last_refreshed } )
            logging.info("Saved consumer (provider) values")

    def on_message(self,client,userdata,msg):
        topic = msg.topic.split("/")

        try:
            if topic[4] == u"refreshed":
                if len(self.processed_values) > 0:
                    now = datetime.now().astimezone()
                    currentIsModified = forecastsIsModified = False
                    totalCount = updateCount = insertCount = 0
                    with self.db.open() as db:
                        for timestamp in self.processed_values:
                            validFrom = datetime.fromtimestamp(int(timestamp))
                            isCurrent = validFrom.day == now.day and validFrom.hour == now.hour
                            update_values = []
                            for field in self.processed_values[timestamp]:
                                totalCount += 1
                                update_values.append(u"`{}`='{}'".format(field,self.processed_values[timestamp][field]))

                            isUpdate = db.hasEntry(validFrom.timestamp())
                            try:
                                if isCurrent or isUpdate:
                                    isModified = db.update(validFrom.timestamp(),update_values)
                                else:
                                    isModified = db.insertOrUpdate(validFrom.timestamp(),update_values)

                                if isModified:
                                    if isCurrent:
                                        currentIsModified = True
                                    forecastsIsModified = True
                                    if isUpdate:
                                        updateCount += 1
                                    else:
                                        insertCount += 1
                            except Exception as e:
                                logging.info(update_values)
                                raise e

                    logging.info("Forecasts processed • Total {} • Queries: {} • Updated: {} • Inserted: {}".format(totalCount, len(self.processed_values),updateCount,insertCount))
                    self.processed_values = {}

                    if forecastsIsModified:
                        self.handler.notifyChangedWeekData()

                    if currentIsModified:
                        with self.db.open() as db:
                            self.current_values = db.getOffset(0)

                        with self.station_fallback_lock:
                            if self.station_fallback_data is not None:
                                for field, value in self._buildFallbackStationValues().items():
                                    if field in self.station_fallback_data and self.station_fallback_data[field] == value:
                                        continue
                                    self.station_fallback_data[field] = value
                                    self.notifyCurrentValue(field, value)

                    self.last_refreshed = now.timestamp()
                else:
                    logging.info("Forcecasts not processed")
            else:
                field = topic[4]
                timestamp = topic[5]

                if timestamp not in self.processed_values:
                    self.processed_values[timestamp] = {}

                self.processed_values[timestamp][field] = msg.payload.decode("utf-8")
        except DBException:
            self.last_error = datetime.now().astimezone().timestamp()
        except Exception as e:
            logging.error("Topic: {}".format(topic))
            logging.error("{}: {}".format(str(e.__class__),str(e)))
            traceback.print_exc()
            self.last_error = datetime.now().astimezone().timestamp()

    def resetIconCache(self):
        self.icon_cache = {}

    def getCachedIcon(self, icon_name):
        if icon_name not in self.icon_cache:
            with open("{}{}".format(self.icon_path, icon_name)) as f:
                self.icon_cache[icon_name] = f.read()
        return self.icon_cache[icon_name]

    def stationValuesOutdated(self):
        return datetime.now().astimezone().timestamp() - self.station_values_last_modified > 60 * 60 * 1

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

            result["currentRainRateInMillimeterPerHour"] = 0
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

        if self.stationValuesOutdated():
            currentRain = self.current_values["precipitationAmountInMillimeter"]
        else:
            currentRain = 0
            currentRainLevel = self.station_values["currentRainLevel"]
            if (currentRainLevel > 0 and self.current_is_raining or currentRainLevel > 2):
                currentRain = 0.1
                currentRainRatePerHour = self.station_values["currentRainRateInMillimeterPerHour"]
                if currentRainRatePerHour > currentRain:
                    currentRain = currentRainRatePerHour

                currentRain1Hour = self.station_values["currentRainLastHourInMillimeter"]
                if currentRain1Hour > currentRain:
                    currentRain = currentRain1Hour
        self.current_is_raining = currentRain > 0
        block.setPrecipitationAmountInMillimeter(currentRain)

        cloudCoverInOcta = self.station_values["currentCloudCoverInOcta"] if not self.stationValuesOutdated() else self.current_values["effectiveCloudCoverInOcta"]
        block.setEffectiveCloudCover(cloudCoverInOcta)

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

        if field in ["currentRainLevel", "currentRainRateInMillimeterPerHour", "currentRainLastHourInMillimeter", "currentCloudCoverInOcta"]:
            if self.station_cloud_timer is not None:
                self.station_cloud_timer.cancel()
            self.station_cloud_timer = threading.Timer(15, self._notifyCloudValue)
            self.station_cloud_timer.start()

    def checkSunriseSunset(self):
        now = datetime.now()
        sunrise, sunset = WeatherHelper.getSunriseAndSunset(self.latitude, self.longitude, now)
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

        is_raining = result["currentRainLevel"] > 0 or result["currentRainLastHourInMillimeter"] > 0
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
        #logging.info(">>>> _applyWeekDay: icon_name: {} - start: {} - end: {}".format(icon_name, current_value.start, current_value.end))
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
                        #logging.info(">>>> DayList: icon_name: {} - start: {} - end: {}".format(icon_name, current_value.start, current_value.end))
                        current_value.setSVG(self.getCachedIcon(icon_name))
                        todayValues.append( current_value )
                        current_value = WeatherBlock( hourlyData['datetime'] )
                    current_value.apply(hourlyData)
                    index += 1

                current_value.setEnd(current_value.getStart() + timedelta(hours=3))
                icon_name = WeatherHelper.convertOctaToSVG(self.latitude, self.longitude, current_value)
                #logging.info(">>>> DayList: icon_name: {} - start: {} - end: {}".format(icon_name, current_value.start, current_value.end))
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
        has_any_update = True if datetime.now().astimezone().timestamp() - self.last_refreshed < 60 * 60 * 2 else False
        has_errors = True if self.last_error != 0 and self.last_refreshed != 0 and self.last_refreshed - self.last_error < 300 else False

        return [
            Metric.buildProcessMetric("weather_service", "consumer_provider", "1" if self.is_running and not has_errors else "0"),
            Metric.buildStateMetric("weather_service", "consumer_provider", "cache_file", "1" if self.valid_cache_file else "0"),
            Metric.buildStateMetric("weather_service", "consumer_provider", "not_outdatet", "1" if has_any_update else "0")
        ]
