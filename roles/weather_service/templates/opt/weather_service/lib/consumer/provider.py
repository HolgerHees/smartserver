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
from lib.helper.forecast import WeatherBlock, WeatherBlockList, WeatherHelper
from lib.helper.constants import CurrentFields, CurrentFieldsList

class CurrentValues():
    FIELD_MAPPINGS = {
        CurrentFields.AIR_TEMPERATURE_IN_CELSIUS: "airTemperatureInCelsius",
        CurrentFields.PERCEIVED_TEMPERATURE_IN_CELSIUS: "feelsLikeTemperatureInCelsius",
        CurrentFields.WIND_GUST_IN_KILOMETER_PER_HOUR: "maxWindSpeedInKilometerPerHour",
        CurrentFields.WIND_SPEED_IN_KILOMETER_PER_HOUR: "windSpeedInKilometerPerHour",
        CurrentFields.RAIN_LAST_HOUR_IN_MILLIMETER: "precipitationAmountInMillimeter",
        CurrentFields.UV_INDEX: "uvIndexWithClouds"
    }

    def __init__(self, db, latitude, longitude, icon_path):
        self.db = db
        self.latitude = latitude
        self.longitude = longitude

        self.icon_path = icon_path
        self.icon_cache = {}

        self.current_is_raining = False

        self.station_values = {}
        self.station_values_last_modified = 0

        self.service_values = {}

        self.current_values = {}

        self._buildCurrentValues()

    def getCurrentValues(self):
        return self.current_values

    def getCurrentValue(self, field):
        return self.current_values[field] if field in self.current_values else None

    def setStationValue(self, field, value):
        if field not in self.current_values or field not in self.station_values or self.station_values[field] != value:
            self.station_values[field] = value
            self.station_values_last_modified = datetime.now().astimezone().timestamp()
            return self._buildCurrentValues()
        else:
            return {}

    def setServiceValues(self, values):
        change_count = sum(1 for k in values if k not in self.service_values or values[k] != self.service_values[k])
        if change_count > 0:
            self.service_values = values
            return self._buildCurrentValues()
        return {}

    def resetIconCache(self):
        self.icon_cache = {}

    def getCachedIcon(self, icon_name):
        if icon_name not in self.icon_cache:
            with open("{}{}".format(self.icon_path, icon_name)) as f:
                self.icon_cache[icon_name] = f.read()
        return self.icon_cache[icon_name]

    def rebuildCloudSVGIfNeeded(self):
        cloud_svg = self._buildCloudSVG()
        if "currentCloudsAsSVG" not in self.current_values or self.current_values["currentCloudsAsSVG"] != cloud_svg:
            self.current_values["currentCloudsAsSVG"] = cloud_svg
            return True
        return False

    def _stationValuesOutdated(self):
        return datetime.now().astimezone().timestamp() - self.station_values_last_modified > 60 * 60 * 1

    def _buildCurrentValues(self):
        current_values = {}
        if not self._stationValuesOutdated():
            current_values = self.station_values.copy()

        for field in CurrentFieldsList.values():
            if field in current_values:
                continue

            mapped_current_field = self.FIELD_MAPPINGS[field] if field in self.FIELD_MAPPINGS else None
            if mapped_current_field is None or mapped_current_field not in self.service_values:
                if field in ["currentRainRateInMillimeterPerHour", "currentRainLastHourInMillimeter", "currentRainLevel"]:
                    current_values[field] = 0
                elif field in ["currentRainDailyInMillimeter"]:
                    end = datetime.now()
                    start = end.replace(hour=0, minute=0, second=0, microsecond=0)
                    with self.db.open() as db:
                        values = db.getRangeSum(start, end, ["precipitationAmountInMillimeter"])
                    current_values["currentRainDailyInMillimeter"] = values["precipitationAmountInMillimeter"]
                else:
                    current_values[field] = -1
            else:
                current_values[field] = self.service_values[mapped_current_field]

        current_values["currentCloudsAsSVG"] = self._buildCloudSVG()

        is_raining = current_values["currentRainLevel"] > 0 or current_values["currentRainLastHourInMillimeter"] > 0
        current_values["currentRainProbabilityInPercent"] = 0 if not self.service_values or not is_raining else self.service_values["precipitationProbabilityInPercent"]
        current_values["currentSunshineDurationInMinutes"] = 0 if not self.service_values else self.service_values["sunshineDurationInMinutes"]

        changed_values = {k: current_values[k] for k in current_values if k not in self.current_values or current_values[k] != self.current_values[k]}
        self.current_values = current_values
        return changed_values

    def _buildCloudSVG(self):
        if not self.service_values:
            return None

        block = WeatherBlock(datetime.now())
        block.apply(self.service_values)

        skip_station_values = self._stationValuesOutdated()
        if skip_station_values or "currentRainLevel" not in self.station_values or "currentRainRateInMillimeterPerHour" not in self.station_values or "currentRainLastHourInMillimeter" not in self.station_values:
            currentRain = self.service_values["precipitationAmountInMillimeter"]
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

        cloudCoverInOcta = self.service_values["effectiveCloudCoverInOcta"] if not skip_station_values or "currentCloudCoverInOcta" not in self.station_values else self.station_values["currentCloudCoverInOcta"]
        block.setEffectiveCloudCover(cloudCoverInOcta)

        return self.getCachedIcon(WeatherHelper.convertOctaToSVG(self.latitude, self.longitude, block))

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

        self.current_values = CurrentValues(self.db, self.latitude, self.longitude, config.icon_path)

        self.is_night = False;

        self.station_cloud_timer = None

        with self.db.open() as db:
            db_values = db.getOffset(0)
            self.current_values.setServiceValues(db_values if db_values else {})

    def start(self):
        self._restore()
        if not os.path.exists(self.dump_path):
            self._dump()

        self.mqtt.subscribe('+/weather/provider/forecast/#', self.on_message)

        self._checkSunriseSunset()
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
                            db_values = db.getOffset(0)
                            _changed_values = self.current_values.setServiceValues(db_values if db_values else {})
                            self._notifyCurrentValues(_changed_values)

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

    def _triggerCloudSVGRebuild(self):
        self.station_cloud_timer = None
        if self.current_values.rebuildCloudSVGIfNeeded():
            self.handler.notifyChangedCurrentData("currentCloudsAsSVG", self.current_values.getCurrentValue("currentCloudsAsSVG"))

    def _checkSunriseSunset(self):
        now = datetime.now()
        sunrise, sunset = WeatherHelper.getSunriseAndSunset(self.latitude, self.longitude, now)
        is_night = ( now <= sunrise or now >= sunset )
        if is_night != self.is_night:
            self.is_night = is_night
            if self.station_cloud_timer is not None:
                self.station_cloud_timer.cancel()
            self._triggerCloudSVGRebuild()

        logging.info("Trigger: checkSunriseSunset => " + str(self.is_night))

        if now < sunrise or now > sunset:
            logging.info("Schedule sunrise: " + sunrise.strftime("%H:%M:%S"))
            schedule.every().day.at(sunrise.strftime("%H:%M:%S")).do(self._checkSunriseSunset)
        else:
            logging.info("Schedule sunset: " + sunset.strftime("%H:%M:%S"))
            schedule.every().day.at(sunset.strftime("%H:%M:%S")).do(self._checkSunriseSunset)

        return schedule.CancelJob

    def _notifyCurrentValues(self, values):
        for field, value in values.items():
            self.handler.notifyChangedCurrentData(field, value)

        if values.keys() & ["currentRainLevel", "currentRainRateInMillimeterPerHour", "currentRainLastHourInMillimeter", "currentCloudCoverInOcta"]:
            if self.station_cloud_timer is not None:
                self.station_cloud_timer.cancel()
            self.station_cloud_timer = threading.Timer(15, self._triggerCloudSVGRebuild)
            self.station_cloud_timer.start()

    def notifyStationValue(self, is_update, field, value, time):
        changed_values = self.current_values.setStationValue(field, value)
        #logging.info("notifyStationValue " + field + " " + str(value) + " " + str(changed_values))
        if is_update:
            self._notifyCurrentValues(changed_values)

    def resetIconCache(self):
        self.current_values.resetIconCache()

    def getCurrentValues(self):
        return self.current_values.getCurrentValues()

    def _applyWeekDay(self, current_value, weekValues):
        current_value.setEnd((current_value.getStart() + timedelta(hours=24)).replace(hour=0, minute=0, second=0))
        icon_name = WeatherHelper.convertOctaToSVG(self.latitude, self.longitude, current_value)
        #logging.info(">>>> _applyWeekDay: icon_name: {} - start: {} - end: {}".format(icon_name, current_value.start, current_value.end))
        current_value.setSVG(self.current_values.getCachedIcon(icon_name))
        weekValues.append(current_value)

    def getWeekValues(self, requested_day = None):
        activeDay = datetime.now() if requested_day is None else datetime.strptime(requested_day, '%Y-%m-%d')
        activeDay = activeDay.replace(hour=0, minute=0, second=0, microsecond=0)

        values = {}

        with self.db.open() as db:
            start = activeDay.replace(hour=0, minute=0, second=0, microsecond=0)
            end = activeDay.replace(hour=23, minute=59, second=59, microsecond=0)

            # DAY VALUES
            todayValues = WeatherBlockList()
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
                        current_value.setSVG(self.current_values.getCachedIcon(icon_name))
                        todayValues.append( current_value )
                        current_value = WeatherBlock( hourlyData['datetime'] )
                    current_value.apply(hourlyData)
                    index += 1

                current_value.setEnd(current_value.getStart() + timedelta(hours=3))
                icon_name = WeatherHelper.convertOctaToSVG(self.latitude, self.longitude, current_value)
                #logging.info(">>>> DayList: icon_name: {} - start: {} - end: {}".format(icon_name, current_value.start, current_value.end))
                current_value.setSVG(self.current_values.getCachedIcon(icon_name))
                todayValues.append(current_value)

            else:
                minTemperature = maxTemperature = maxWindSpeed = sumSunshine = sumRain = activeDay = None

            values["dayList"] = todayValues.toDictList()
            values["dayActive"] = activeDay.isoformat()
            values["dayMinTemperature"] = minTemperature
            values["dayMaxTemperature"] = maxTemperature
            values["dayMaxWindSpeed"] = maxWindSpeed
            values["daySumSunshine"] = sumSunshine
            values["daySumRain"] = sumRain

            # WEEK VALUES
            weekValues = WeatherBlockList()

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

            values["weekList"] = weekValues.toDictList()
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
            todayValues = WeatherBlockList()
            if len(dayList) > 0:
                blockConfigs = []

                current_value = None;
                hour_count = 0
                for hourlyData in dayList:
                    hour = hourlyData['datetime'].hour;
                    if hour_count >= 5:
                        current_value.setEnd(hourlyData['datetime'])
                        icon_name = WeatherHelper.convertOctaToSVG(self.latitude, self.longitude, current_value)
                        current_value.setSVG(self.current_values.getCachedIcon(icon_name))
                        todayValues.append(current_value)
                        current_value = None
                        hour_count = 0

                    if current_value is None:
                        current_value = WeatherBlock( hourlyData['datetime'] )

                    current_value.apply(hourlyData)
                    if todayValues.getSize() == 4:
                        break

                    hour_count += 1

                minTemperature, maxTemperature, maxWindSpeed, sumSunshine, sumRain = WeatherHelper.calculateSummary(dayList)
            else:
                minTemperature = maxTemperature = maxWindSpeed = sumSunshine = sumRain = None

            values["dayList"] = todayValues.toDictList()
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
