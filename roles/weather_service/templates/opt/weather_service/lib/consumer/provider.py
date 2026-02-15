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
from lib.helper.constants import CurrentFields, CurrentFieldsList, ForecastFields

class CurrentValues():
    CURRENT_FALLBACK_MAPPING = {
        CurrentFields.AIR_TEMPERATURE_IN_CELSIUS:       ForecastFields.AIR_TEMPERATURE_IN_CELSIUS,
        CurrentFields.PERCEIVED_TEMPERATURE_IN_CELSIUS: ForecastFields.FEELS_LIKE_TEMPERATURE_IN_CELSIUS,

        CurrentFields.AIR_HUMIDITY_IN_PERCENT:          ForecastFields.RELATIVE_HUMIDITY_IN_PERCENT,

        CurrentFields.WIND_DIRECTION_IN_DEGREE:         ForecastFields.WIND_DIRECTION_IN_DEGREE,
        CurrentFields.WIND_SPEED_IN_KILOMETER_PER_HOUR: ForecastFields.WIND_SPEED_IN_KILOMETER_PER_HOUR,
        CurrentFields.WIND_GUST_IN_KILOMETER_PER_HOUR:  ForecastFields.MAX_WIND_SPEED_IN_KILOMETER_PER_HOUR,

        CurrentFields.CLOUD_COVER_IN_OCTA:              ForecastFields.EFFECTVE_CLOUD_COVER_IN_OCTA,

        CurrentFields.RAIN_LAST_HOUR_IN_MILLIMETER:     ForecastFields.PERCIPITATION_AMOUNT_IN_MILLIMETER,
        CurrentFields.UV_INDEX:                         ForecastFields.UV_INDEX_WITH_CLOUDS
    }

    def __init__(self, db, latitude, longitude, icon_path, notify_callback):
        self.db = db
        self.latitude = latitude
        self.longitude = longitude

        self.icon_path = icon_path
        self.icon_cache = {}

        self.notify_callback = notify_callback

        self.station_cloud_timer = None
        self.current_is_raining = False
        self.current_is_night = False

        self.station_values = {}
        self.station_values_last_modified = 0

        self.service_values = {}

        self.current_values = {}

        self._buildCurrentValues()

    def resetIconCache(self):
        self.icon_cache = {}

    def getCachedIcon(self, icon_name):
        if icon_name not in self.icon_cache:
            with open("{}{}".format(self.icon_path, icon_name)) as f:
                self.icon_cache[icon_name] = f.read()
        return self.icon_cache[icon_name]

    def checkSunriseSunset(self):
        now = datetime.now()
        sunrise, sunset = WeatherHelper.getSunriseAndSunset(self.latitude, self.longitude, now)
        current_is_night = ( now <= sunrise or now >= sunset )
        if current_is_night != self.current_is_night:
            self.current_is_night = current_is_night
            if self.station_cloud_timer is not None:
                self.station_cloud_timer.cancel()
            self._rebuildCloudSVGIfNeeded()

        logging.info("Trigger: checkSunriseSunset => " + str(self.current_is_night))

        if now < sunrise or now > sunset:
            logging.info("Schedule sunrise: " + sunrise.strftime("%H:%M:%S"))
            schedule.every().day.at(sunrise.strftime("%H:%M:%S")).do(self.checkSunriseSunset)
        else:
            logging.info("Schedule sunset: " + sunset.strftime("%H:%M:%S"))
            schedule.every().day.at(sunset.strftime("%H:%M:%S")).do(self.checkSunriseSunset)

        return schedule.CancelJob

    def getCurrentValues(self):
        return self.current_values

    def getCurrentValue(self, field):
        return self.current_values[field] if field in self.current_values else None

    def setStationValue(self, field, value):
        if field not in self.current_values or field not in self.station_values or self.station_values[field] != value:
            self.station_values[field] = value
            self.station_values_last_modified = datetime.now().astimezone().timestamp()
            self._buildCurrentValues()

    def setServiceValues(self, values):
        change_count = sum(1 for k in values if k not in self.service_values or values[k] != self.service_values[k])
        if change_count > 0:
            self.service_values = values
            self._buildCurrentValues()

    def _rebuildCloudSVGIfNeeded(self):
        if self.station_cloud_timer is not None:
            self.station_cloud_timer.cancel()
            self.station_cloud_timer = None

        cloud_svg = self._buildCloudSVG()
        if CurrentFields.CLOUDS_AS_SVG not in self.current_values or self.current_values[CurrentFields.CLOUDS_AS_SVG] != cloud_svg:
            self.current_values[CurrentFields.CLOUDS_AS_SVG] = cloud_svg
            self.notify_callback({CurrentFields.CLOUDS_AS_SVG: cloud_svg})

    def _buildCurrentValues(self):
        current_values = {}
        if not self._isStationOutdated():
            current_values = self.station_values.copy()

        for field in CurrentFieldsList.values():
            if field in current_values:
                continue

            mapped_current_field = self.CURRENT_FALLBACK_MAPPING[field] if field in self.CURRENT_FALLBACK_MAPPING else None
            if mapped_current_field is None or mapped_current_field not in self.service_values:
                if field in [CurrentFields.RAIN_RATE_IN_MILLIMETER_PER_HOUR, CurrentFields.RAIN_LAST_HOUR_IN_MILLIMETER, CurrentFields.RAIN_LEVEL]:
                    current_values[field] = 0
                elif field in [CurrentFields.RAIN_DAILY_IN_MILLIMETER]:
                    end = datetime.now()
                    start = end.replace(hour=0, minute=0, second=0, microsecond=0)
                    with self.db.open() as db:
                        values = db.getRangeSum(start, end, [ForecastFields.PERCIPITATION_AMOUNT_IN_MILLIMETER])
                    current_values[CurrentFields.RAIN_DAILY_IN_MILLIMETER] = values[ForecastFields.PERCIPITATION_AMOUNT_IN_MILLIMETER]
                else:
                    current_values[field] = -1
            else:
                current_values[field] = self.service_values[mapped_current_field]

        current_values[CurrentFields.CLOUDS_AS_SVG] = self._buildCloudSVG()

        is_raining = current_values[CurrentFields.RAIN_LEVEL] > 0 or current_values[CurrentFields.RAIN_LAST_HOUR_IN_MILLIMETER] > 0
        current_values[CurrentFields.RAIN_PROBABILITY_IN_PERCENT] = 0 if not self.service_values or not is_raining else self.service_values[ForecastFields.PERCIPITATION_PROBAILITY_IN_PERCENT]
        current_values[CurrentFields.SUNSHINE_DURATION_IN_MINUTES] = 0 if not self.service_values else self.service_values[ForecastFields.SUNSHINE_DURATION_IN_MINUTES]

        changed_values = {k: current_values[k] for k in current_values if k not in self.current_values or current_values[k] != self.current_values[k]}
        self.current_values = current_values

        self.notify_callback(changed_values)

    def _buildCloudSVG(self):
        if not self.service_values:
            return None

        block = WeatherBlock(datetime.now())
        block.apply(self.service_values)

        skip_station_values = self._isStationOutdated()
        if skip_station_values or CurrentFields.RAIN_LEVEL not in self.station_values or CurrentFields.RAIN_RATE_IN_MILLIMETER_PER_HOUR not in self.station_values or CurrentFields.RAIN_LAST_HOUR_IN_MILLIMETER not in self.station_values:
            currentRain = self.service_values[ForecastFields.PERCIPITATION_AMOUNT_IN_MILLIMETER]
        else:
            currentRain = 0
            currentRainLevel = self.station_values[CurrentFields.RAIN_LEVEL]
            if (currentRainLevel > 0 and self.current_is_raining or currentRainLevel > 2):
                currentRain = 0.1
                currentRainRatePerHour = self.station_values[CurrentFields.RAIN_RATE_IN_MILLIMETER_PER_HOUR]
                if currentRainRatePerHour > currentRain:
                    currentRain = currentRainRatePerHour

                currentRain1Hour = self.station_values[CurrentFields.RAIN_LAST_HOUR_IN_MILLIMETER]
                if currentRain1Hour > currentRain:
                    currentRain = currentRain1Hour
        self.current_is_raining = currentRain > 0
        block.setPrecipitationAmountInMillimeter(currentRain)

        cloudCoverInOcta = self.service_values[ForecastFields.EFFECTVE_CLOUD_COVER_IN_OCTA] if not skip_station_values or CurrentFields.CLOUD_COVER_IN_OCTA not in self.station_values else self.station_values[CurrentFields.CLOUD_COVER_IN_OCTA]
        block.setEffectiveCloudCover(cloudCoverInOcta)

        return self.getCachedIcon(WeatherHelper.convertOctaToSVG(self.latitude, self.longitude, block))

    def _isStationOutdated(self):
        return datetime.now().astimezone().timestamp() - self.station_values_last_modified > 60 * 60 * 1

class ProviderConsumer():
    '''Handler client'''
    def __init__(self, config, mqtt, db, handler ):
        self.config = config
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

        self.current_values = CurrentValues(self.db, self.latitude, self.longitude, config.icon_path, self._notifyCurrentValues)

        with self.db.open() as db:
            db_values = db.getOffset(0)
            self.current_values.setServiceValues(db_values if db_values else {})

    def start(self):
        self._restore()
        if not os.path.exists(self.dump_path):
            self._dump()

        logging.info("{}/#".format(self.config.mqtt_forecast_topic))
        self.mqtt.subscribe("{}/#".format(self.config.mqtt_forecast_topic), self.on_message)

        self.current_values.checkSunriseSunset()
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
                            self.current_values.setServiceValues(db_values if db_values else {})

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

    def _notifyCurrentValues(self, values):
        for field, value in values.items():
            self.handler.notifyChangedCurrentData(field, value)

    def notifyStationValue(self, is_update, field, value, time):
        self.current_values.setStationValue(field, value)

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
