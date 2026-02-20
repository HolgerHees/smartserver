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
from lib.helper.fields import CurrentFields, ForecastFields, CurrentFieldFallbackMappings


class ProviderConsumer():
    def __init__(self, config, mqtt, db, astro, handler ):
        latitude, longitude = config.location.split(",")

        self.mqtt = mqtt
        self.mqtt_provider_topic = "{}/#".format(config.mqtt_consume_provider_topic)

        self.db = db
        self.astro = astro
        self.handler = handler

        self.is_running = False

        self.dump_path = "{}consumer_provider.json".format(config.lib_path)
        self.version = 2
        self.valid_cache_file = True

        self.processed_values = {}

        self.last_error = 0
        self.last_refreshed = 0

        self.image_factory = CloudImageFactory(config.icon_path)
        self.current_data_factory = CurrentDataFactory(self.db, self.astro, self.image_factory, self._notifyCurrentValues)

    def start(self):
        self._restore()
        if not os.path.exists(self.dump_path):
            self._dump()

        self.mqtt.subscribe(self.mqtt_provider_topic, self.on_message)

        with self.db.open() as db:
            db_values = db.getOffset(0)
            self.current_data_factory.setServiceValues(db_values if db_values else {})

        self.current_data_factory.checkSunriseSunset()
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
                            try:
                                validFrom = datetime.fromtimestamp(int(timestamp))
                                isCurrent = validFrom.day == now.day and validFrom.hour == now.hour
                                update_values = []
                                for field in self.processed_values[timestamp]:
                                    if field not in ForecastFields:
                                        raise Exception("Unknown forecast field '{}'. Only follwoing values are allowed {}".format(field, list(ForecastFields)))
                                    totalCount += 1
                                    update_values.append(u"`{}`='{}'".format(field,self.processed_values[timestamp][field]))

                                isUpdate = db.hasEntry(validFrom.timestamp())

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
                                logging.error(update_values)
                                raise e

                    logging.info("Forecasts processed • Total {} • Queries: {} • Updated: {} • Inserted: {}".format(totalCount, len(self.processed_values),updateCount,insertCount))
                    self.processed_values = {}

                    if forecastsIsModified:
                        self.handler.notifyChangedWeekData()

                    if currentIsModified:
                        with self.db.open() as db:
                            db_values = db.getOffset(0)
                            self.current_data_factory.setServiceValues(db_values if db_values else {})

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
        self.current_data_factory.setStationValue(field, value)

    def resetIconCache(self):
        self.image_factory.reset()

    def getCurrentValues(self):
        return self.current_data_factory.getCurrentValues()

    def _applyCloudSVG(self, icons, icon_names):
        for icon_name in icon_names:
            if icon_name in icons:
                continue
            icons[icon_name] = self.image_factory.get(icon_name)

    def _calculateSummary(self, dataList):
        minTemperature = dataList[0][ForecastFields.AIR_TEMPERATURE_IN_CELSIUS];
        maxTemperature = dataList[0][ForecastFields.AIR_TEMPERATURE_IN_CELSIUS];
        maxWindSpeed = dataList[0][ForecastFields.WIND_SPEED_IN_KILOMETER_PER_HOUR];
        sumSunshine = 0;
        sumRain = 0;

        for entry in dataList:
            if minTemperature > entry[ForecastFields.AIR_TEMPERATURE_IN_CELSIUS]:
                minTemperature = entry[ForecastFields.AIR_TEMPERATURE_IN_CELSIUS]
            if maxTemperature < entry[ForecastFields.AIR_TEMPERATURE_IN_CELSIUS]:
                maxTemperature = entry[ForecastFields.AIR_TEMPERATURE_IN_CELSIUS]
            if maxWindSpeed < entry[ForecastFields.WIND_SPEED_IN_KILOMETER_PER_HOUR]:
                maxWindSpeed = entry[ForecastFields.WIND_SPEED_IN_KILOMETER_PER_HOUR]

            sumSunshine += entry[ForecastFields.SUNSHINE_DURATION_IN_MINUTES]
            sumRain += entry[ForecastFields.PRECIPITATION_AMOUNT_IN_MILLIMETER]

        return [ minTemperature, maxTemperature, maxWindSpeed, sumSunshine, sumRain ]

    def getWeekValues(self, requested_day = None):
        activeDay = datetime.now() if requested_day is None else datetime.strptime(requested_day, '%Y-%m-%d')
        activeDay = activeDay.replace(hour=0, minute=0, second=0, microsecond=0)

        values = {}

        with self.db.open() as db:
            start = activeDay.replace(hour=0, minute=0, second=0, microsecond=0)
            end = activeDay.replace(hour=23, minute=59, second=59, microsecond=0)

            cloudIcons = {}

            # DAY VALUES
            todayValues = WeatherBlockList()
            dayList = db.getRangeList(start, end)
            if len(dayList) > 0:
                minTemperature, maxTemperature, maxWindSpeed, sumSunshine, sumRain = self._calculateSummary(dayList)

                current_value = WeatherBlock(dayList[0]['datetime'].astimezone())

                index = 0;
                for hourlyData in dayList:
                    if index > 0 and index % 3 == 0:
                        #_datetime = hourlyData['datetime'].replace(minute=0, second=0);
                        current_value.setEnd(hourlyData['datetime'].astimezone())
                        current_value.initCloudIcons(self.astro.getSunrise(), self.astro.getSunset(), self.image_factory.build, True)
                        self._applyCloudSVG(cloudIcons, current_value.getCloudIconNames())
                        todayValues.append( current_value )
                        current_value = WeatherBlock(hourlyData['datetime'].astimezone())
                    current_value.apply(hourlyData['datetime'].astimezone(), hourlyData)
                    index += 1

                current_value.setDuration(timedelta(hours=3))
                current_value.initCloudIcons(self.astro.getSunrise(), self.astro.getSunset(), self.image_factory.build, True)
                self._applyCloudSVG(cloudIcons, current_value.getCloudIconNames())
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
                minTemperatureWeekly, maxTemperatureWeekly, maxWindSpeedWeekly, sumSunshineWeekly, sumRainWeekly = self._calculateSummary(weekList)

                current_start = weekList[0]['datetime'].astimezone().replace(hour=0, minute=0, second=0)
                current_value = WeatherBlock(current_start)
                index = 1
                for hourlyData in weekList:
                    _current_start = hourlyData['datetime'].astimezone().replace(hour=0, minute=0, second=0);
                    if _current_start != current_start:
                        current_value.setDuration(timedelta(hours=24))
                        current_value.initCloudIcons(self.astro.getSunrise(), self.astro.getSunset(), self.image_factory.build, False)
                        self._applyCloudSVG(cloudIcons, current_value.getCloudIconNames())
                        weekValues.append(current_value)
                        current_start = _current_start
                        current_value = WeatherBlock(_current_start)
                    current_value.apply(hourlyData['datetime'].astimezone(), hourlyData)
                    index += 1

                current_value.setDuration(timedelta(hours=24))
                current_value.initCloudIcons(self.astro.getSunrise(), self.astro.getSunset(), self.image_factory.build, False)
                self._applyCloudSVG(cloudIcons, current_value.getCloudIconNames())
                weekValues.append(current_value)
            else:
                minTemperatureWeekly = maxTemperatureWeekly = maxWindSpeedWeekly = sumSunshineWeekly = sumRainWeekly = None

            values["cloudIconMap"] = cloudIcons
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

            cloudIcons = {}

            dayList = db.getRangeList(start, end)
            values = {}
            todayValues = WeatherBlockList()
            if len(dayList) > 0:
                blockConfigs = []

                current_value = None;
                hour_count = 0
                for hourlyData in dayList:
                    hour = hourlyData['datetime'].astimezone().hour;
                    if hour_count >= 5:
                        current_value.setEnd(hourlyData['datetime'].astimezone())
                        current_value.initCloudIcons(self.astro.getSunrise(), self.astro.getSunset(), self.image_factory.build, False)
                        self._applyCloudSVG(cloudIcons, current_value.getCloudIconNames())
                        todayValues.append(current_value)
                        current_value = None
                        hour_count = 0

                    if current_value is None:
                        current_value = WeatherBlock(hourlyData['datetime'].astimezone())

                    current_value.apply(hourlyData['datetime'].astimezone(), hourlyData)
                    if todayValues.getSize() == 4:
                        break

                    hour_count += 1

                minTemperature, maxTemperature, maxWindSpeed, sumSunshine, sumRain = self._calculateSummary(dayList)
            else:
                minTemperature = maxTemperature = maxWindSpeed = sumSunshine = sumRain = None

            values["cloudIconMap"] = cloudIcons
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

class CloudImageFactory():
    sunConfig = {
        'day': [ 'day', 'cloudy-day-0', 'cloudy-day-1', 'cloudy-day-2', 'cloudy' ],
        'night': [ 'night', 'cloudy-night-0', 'cloudy-night-1', 'cloudy-night-2', 'cloudy' ]
    }

    def __init__(self, icon_path):
        self.icon_path = icon_path
        self.icon_cache = {}

    def reset(self):
        self.icon_cache = {}

    def get(self, icon_name):
        if icon_name not in self.icon_cache:
            with open("{}{}".format(self.icon_path, icon_name)) as f:
                self.icon_cache[icon_name] = f.read()
        return self.icon_cache[icon_name]

    def build(self, isNight, cloudCover, precipitationAmountInMillimeter, precipitationProbabilityInPercent, freezingRainProbabilityInPercent, hailProbabilityInPercent, snowfallProbabilityInPercent, thunderstormProbabilityInPercent):
        cloudIndex = 0
        if cloudCover >= 6:
            cloudIndex = 4
        elif cloudCover >= 4.5:
            cloudIndex = 3
        elif cloudCover >= 3.0:
            cloudIndex = 2
        elif cloudCover >= 1.5:
            cloudIndex = 1

        if ( precipitationProbabilityInPercent >= 30 and precipitationAmountInMillimeter > 0 ) or ( precipitationProbabilityInPercent >= 25 and precipitationAmountInMillimeter > 0.5 ):
            if precipitationAmountInMillimeter >= 1.3:
                amount = 4
            elif precipitationAmountInMillimeter >= 0.9:
                amount = 3
            elif precipitationAmountInMillimeter >= 0.5:
                amount = 2
            else:
                amount = 1

            rain_type = 'snowflake' if freezingRainProbabilityInPercent > 10 or hailProbabilityInPercent > 10 or snowfallProbabilityInPercent > 10 else 'raindrop'
            rain_type = "{}{}".format(rain_type, amount)
        else:
            rain_type = 'none'

        thunder_type = "thunder" if thunderstormProbabilityInPercent >= 15 else 'none'

        if cloudIndex == 0 and ( rain_type != "none" or thunder_type != "none" ):
            cloudIndex = 1

        icon = self.sunConfig[ 'night' if isNight else 'day' ][cloudIndex];

        return "{}_{}_{}_grayscaled.svg".format(icon, rain_type, thunder_type)

class CurrentDataFactory():
    def __init__(self, db, astro, image_factory, notify_callback):
        self.db = db
        self.astro = astro
        self.image_factory = image_factory

        self.notify_callback = notify_callback

        self.current_is_raining = False
        self.current_is_night = False

        self.station_values = {}
        self.station_values_last_modified = 0

        self.service_values = {}

        self.current_values = {}

        self.build_lock = threading.Lock()

        self._buildCurrentValues()

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

    def checkSunriseSunset(self):
        now = datetime.now().astimezone()
        sunrise = self.astro.getSunrise()
        sunset = self.astro.getSunset()
        current_is_night = ( now <= sunrise or now >= sunset )
        if current_is_night != self.current_is_night:
            self.current_is_night = current_is_night

            changed_values = None
            with self.build_lock:
                cloud_svg = self._buildCloudSVG()
                if CurrentFields.CLOUDS_AS_SVG not in self.current_values or self.current_values[CurrentFields.CLOUDS_AS_SVG] != cloud_svg:
                        self.current_values[CurrentFields.CLOUDS_AS_SVG] = cloud_svg
                        changed_values = {CurrentFields.CLOUDS_AS_SVG: cloud_svg}
            if changed_values is not None:
                self.notify_callback(changed_values)

        if now < sunrise or now > sunset:
            logging.info("Sunrise/Sunset check: is night {}, Schedule next check at sunrise: {}".format(str(self.current_is_night), sunrise.strftime("%H:%M:%S")))
            schedule.every().day.at(sunrise.strftime("%H:%M:%S")).do(self.checkSunriseSunset)
        else:
            logging.info("Sunrise/Sunset check: is night {}, Schedule next check at sunset: {}".format(str(self.current_is_night), sunset.strftime("%H:%M:%S")))
            schedule.every().day.at(sunset.strftime("%H:%M:%S")).do(self.checkSunriseSunset)

        return schedule.CancelJob

    def _buildCurrentValues(self):
        with self.build_lock:
            current_values = {}
            if not self._isStationOutdated():
                current_values = self.station_values.copy()

            for field in CurrentFields:
                if field in current_values:
                    continue

                mapped_current_field = CurrentFieldFallbackMappings[field] if field in CurrentFieldFallbackMappings else None
                if mapped_current_field is None or mapped_current_field not in self.service_values:
                    if field in [CurrentFields.PRECIPITATION_RATE_IN_MILLIMETER_PER_HOUR, CurrentFields.PRECIPITATION_AMOUNT_IN_MILLIMETER, CurrentFields.PRECIPITATION_LEVEL]:
                        current_values[field] = 0
                    elif field in [CurrentFields.PRECIPITATION_DAILY_IN_MILLIMETER]:
                        end = datetime.now()
                        start = end.replace(hour=0, minute=0, second=0, microsecond=0)
                        with self.db.open() as db:
                            values = db.getRangeSum(start, end, [ForecastFields.PRECIPITATION_AMOUNT_IN_MILLIMETER])
                        current_values[CurrentFields.PRECIPITATION_DAILY_IN_MILLIMETER] = values[ForecastFields.PRECIPITATION_AMOUNT_IN_MILLIMETER]
                    else:
                        current_values[field] = -1
                else:
                    current_values[field] = self.service_values[mapped_current_field]

            current_values[CurrentFields.CLOUDS_AS_SVG] = self._buildCloudSVG()

            is_raining = current_values[CurrentFields.PRECIPITATION_LEVEL] > 0 or current_values[CurrentFields.PRECIPITATION_AMOUNT_IN_MILLIMETER] > 0
            current_values[CurrentFields.PRECIPITATION_PROBABILITY_IN_PERCENT] = 0 if not self.service_values or not is_raining else self.service_values[ForecastFields.PRECIPITATION_PROBABILITY_IN_PERCENT]
            current_values[CurrentFields.SUNSHINE_DURATION_IN_MINUTES] = 0 if not self.service_values else self.service_values[ForecastFields.SUNSHINE_DURATION_IN_MINUTES]

            changed_values = {k: current_values[k] for k in current_values if k not in self.current_values or current_values[k] != self.current_values[k]}
            self.current_values = current_values

        self.notify_callback(changed_values)

    def _buildCloudSVG(self):
        if not self.service_values:
            return None

        skip_station_values = self._isStationOutdated()
        if skip_station_values or CurrentFields.PRECIPITATION_LEVEL not in self.station_values or CurrentFields.PRECIPITATION_RATE_IN_MILLIMETER_PER_HOUR not in self.station_values or CurrentFields.PRECIPITATION_AMOUNT_IN_MILLIMETER not in self.station_values:
            currentRain = self.service_values[ForecastFields.PRECIPITATION_AMOUNT_IN_MILLIMETER]
        else:
            currentRain = 0
            currentRainLevel = self.station_values[CurrentFields.PRECIPITATION_LEVEL]
            if (currentRainLevel > 0 and self.current_is_raining or currentRainLevel > 2):
                currentRain = 0.1
                currentRainRatePerHour = self.station_values[CurrentFields.PRECIPITATION_RATE_IN_MILLIMETER_PER_HOUR]
                if currentRainRatePerHour > currentRain:
                    currentRain = currentRainRatePerHour

                currentRain1Hour = self.station_values[CurrentFields.PRECIPITATION_AMOUNT_IN_MILLIMETER]
                if currentRain1Hour > currentRain:
                    currentRain = currentRain1Hour
        self.current_is_raining = currentRain > 0

        cloudCoverInOcta = self.service_values[ForecastFields.CLOUD_COVER_IN_OCTA] if not skip_station_values or CurrentFields.CLOUD_COVER_IN_OCTA not in self.station_values else self.station_values[CurrentFields.CLOUD_COVER_IN_OCTA]

        #convertOctaToSVG(latitude, longitude, datetime, cloudCover, maxPrecipitationAmountInMillimeter, precipitationProbabilityInPercent, thunderstormProbabilityInPercent, isSnowing)
        #block = WeatherBlock(datetime.now())
        #block.apply(block_data)

        #date, cloudCover, precipitationAmountInMillimeter, precipitationProbabilityInPercent, freezingRainProbabilityInPercent, hailProbabilityInPercent, snowfallProbabilityInPercent, thunderstormProbabilityInPercent, isSnowing

        now = datetime.now().astimezone()
        icon_name = self.image_factory.build(
            isNight = ( now < self.astro.getSunrise() or now > self.astro.getSunset() ),
            cloudCover = cloudCoverInOcta,
            precipitationAmountInMillimeter = currentRain,
            precipitationProbabilityInPercent = 100 if self.current_is_raining > 0 else 0,
            freezingRainProbabilityInPercent = self.service_values[ForecastFields.FREEZING_RAIN_PROBABILITY_IN_PERCENT],
            hailProbabilityInPercent = self.service_values[ForecastFields.HAIL_PROBABILITY_IN_PERCENT],
            snowfallProbabilityInPercent = self.service_values[ForecastFields.SNOWFALL_PROBABILITY_IN_PERCENT],
            thunderstormProbabilityInPercent = self.service_values[ForecastFields.THUNDERSTORM_PROBABILITY_IN_PERCENT]
        )

        return self.image_factory.get(icon_name)

    def _isStationOutdated(self):
        return datetime.now().astimezone().timestamp() - self.station_values_last_modified > 60 * 60 * 1

class WeatherBlockList():
    def __init__(self):
        self.block_list = []

    def append(self, block):
        self.block_list.append(block)

    def toDictList(self):
        result = []
        for block in self.block_list:
            result.append(block.toDict())
        return result

    def getSize(self):
        return len(self.block_list)

class WeatherBlock():
    def __init__(self, start):
        self.start = start
        self.end = start

        self.airTemperatureInCelsius = -100
        self.feelsLikeTemperatureInCelsius = -100

        self.windDirectionInDegree= 0
        self.windSpeedInKilometerPerHour= 0

        self.cloudCoverInOcta= 0

        self.thunderstormProbabilityInPercent= 0
        self.freezingRainProbabilityInPercent= 0
        self.hailProbabilityInPercent= 0
        self.snowfallProbabilityInPercent= 0

        self.precipitationProbabilityInPercent= 0
        self.precipitationAmountInMillimeter= 0

        self.weatherCode = -100
        self.sunshineDurationInMinutes= 0

        self.minAirTemperatureInCelsius = None
        self.maxAirTemperatureInCelsius = None
        self.minCloudCoverInOcta = None
        self.maxCloudCoverInOcta = None
        self.maxPrecipitationAmountInMillimeter = None

        self.cloudIconNames = []
        self.hourlyData = []

    def toDict(self):
        result = {}
        for key, value in self.__dict__.items():
            if key in ("hourlyData"):
                continue

            if key in ["start", "end"]:
                result[key] = value.isoformat()
            else:
                result[key] = value
        return result

    def setEnd(self, end):
        self.end = end

    def setDuration(self, timedelta):
        self.end = self.start + timedelta

    def initCloudIcons(self, sunrise, sunset, getCloudSVGCallback, detailedIcons ):
        icons = []

        start = self.hourlyData[0][0]
        end = self.hourlyData[-1][0]

        timerange = int( ( end - start ).total_seconds() / 60 )
        ref_date = start + timedelta(minutes=timerange / 2)

        if detailedIcons:
            for date, values in self.hourlyData:
                ref_date = date.replace(year=sunrise.year, month=sunrise.month, day=sunrise.day)
                icon_name = getCloudSVGCallback(
                    isNight = ( ref_date < sunrise or ref_date > sunset ),
                    cloudCover = values[ForecastFields.CLOUD_COVER_IN_OCTA],
                    precipitationAmountInMillimeter = values[ForecastFields.PRECIPITATION_AMOUNT_IN_MILLIMETER],
                    precipitationProbabilityInPercent = values[ForecastFields.PRECIPITATION_PROBABILITY_IN_PERCENT],
                    freezingRainProbabilityInPercent = values[ForecastFields.FREEZING_RAIN_PROBABILITY_IN_PERCENT],
                    hailProbabilityInPercent = values[ForecastFields.HAIL_PROBABILITY_IN_PERCENT],
                    snowfallProbabilityInPercent = values[ForecastFields.SNOWFALL_PROBABILITY_IN_PERCENT],
                    thunderstormProbabilityInPercent = values[ForecastFields.THUNDERSTORM_PROBABILITY_IN_PERCENT]
                )
                icons.append(icon_name)
        else:
            icon_name = getCloudSVGCallback(
                isNight = ( ref_date < sunrise or ref_date > sunset ),
                cloudCover = self.cloudCoverInOcta,
                precipitationAmountInMillimeter = self.maxPrecipitationAmountInMillimeter,
                precipitationProbabilityInPercent = self.precipitationProbabilityInPercent,
                freezingRainProbabilityInPercent = self.freezingRainProbabilityInPercent,
                hailProbabilityInPercent = self.hailProbabilityInPercent,
                snowfallProbabilityInPercent = self.snowfallProbabilityInPercent,
                thunderstormProbabilityInPercent = self.thunderstormProbabilityInPercent
            )
            icons.append(icon_name)
        self.cloudIconNames = icons

    def getCloudIconNames(self):
        return self.cloudIconNames

    def apply( self, date, values ):
        self.hourlyData.append([date, values])

        self.sunshineDurationInMinutes += values[ForecastFields.SUNSHINE_DURATION_IN_MINUTES]
        self.precipitationAmountInMillimeter += values[ForecastFields.PRECIPITATION_AMOUNT_IN_MILLIMETER]

        if self.maxPrecipitationAmountInMillimeter is None or self.maxPrecipitationAmountInMillimeter <= values[ForecastFields.PRECIPITATION_AMOUNT_IN_MILLIMETER]:
            self.maxPrecipitationAmountInMillimeter = values[ForecastFields.PRECIPITATION_AMOUNT_IN_MILLIMETER]

        if self.airTemperatureInCelsius < values[ForecastFields.AIR_TEMPERATURE_IN_CELSIUS]:
            self.airTemperatureInCelsius = values[ForecastFields.AIR_TEMPERATURE_IN_CELSIUS]

        if self.minAirTemperatureInCelsius is None or self.minAirTemperatureInCelsius > values[ForecastFields.AIR_TEMPERATURE_IN_CELSIUS]:
            self.minAirTemperatureInCelsius = values[ForecastFields.AIR_TEMPERATURE_IN_CELSIUS]

        if self.maxAirTemperatureInCelsius is None or self.maxAirTemperatureInCelsius < values[ForecastFields.AIR_TEMPERATURE_IN_CELSIUS]:
            self.maxAirTemperatureInCelsius = values[ForecastFields.AIR_TEMPERATURE_IN_CELSIUS]

        if self.feelsLikeTemperatureInCelsius < values[ForecastFields.FEELS_LIKE_TEMPERATURE_IN_CELSIUS]:
            self.feelsLikeTemperatureInCelsius = values[ForecastFields.FEELS_LIKE_TEMPERATURE_IN_CELSIUS]

        if self.cloudCoverInOcta < values[ForecastFields.CLOUD_COVER_IN_OCTA]:
            self.cloudCoverInOcta = values[ForecastFields.CLOUD_COVER_IN_OCTA]

        if self.minCloudCoverInOcta is None or self.minCloudCoverInOcta > values[ForecastFields.CLOUD_COVER_IN_OCTA]:
            self.minCloudCoverInOcta = values[ForecastFields.CLOUD_COVER_IN_OCTA]

        if self.maxCloudCoverInOcta is None or self.maxCloudCoverInOcta < values[ForecastFields.CLOUD_COVER_IN_OCTA]:
            self.maxCloudCoverInOcta = values[ForecastFields.CLOUD_COVER_IN_OCTA]

        if self.windSpeedInKilometerPerHour < values[ForecastFields.WIND_SPEED_IN_KILOMETER_PER_HOUR]:
            self.windSpeedInKilometerPerHour = values[ForecastFields.WIND_SPEED_IN_KILOMETER_PER_HOUR]
            self.windDirectionInDegree = values[ForecastFields.WIND_DIRECTION_IN_DEGREE]

        if self.weatherCode < values[ForecastFields.WEATHER_CODE]:
            self.weatherCode = values[ForecastFields.WEATHER_CODE]

        if self.thunderstormProbabilityInPercent < values[ForecastFields.THUNDERSTORM_PROBABILITY_IN_PERCENT]:
            self.thunderstormProbabilityInPercent = values[ForecastFields.THUNDERSTORM_PROBABILITY_IN_PERCENT]

        if values[ForecastFields.PRECIPITATION_AMOUNT_IN_MILLIMETER] > 0:
            if self.freezingRainProbabilityInPercent < values[ForecastFields.FREEZING_RAIN_PROBABILITY_IN_PERCENT]:
                self.freezingRainProbabilityInPercent = values[ForecastFields.FREEZING_RAIN_PROBABILITY_IN_PERCENT]

            if self.hailProbabilityInPercent < values[ForecastFields.HAIL_PROBABILITY_IN_PERCENT]:
                self.hailProbabilityInPercent = values[ForecastFields.HAIL_PROBABILITY_IN_PERCENT]

            if self.snowfallProbabilityInPercent < values[ForecastFields.SNOWFALL_PROBABILITY_IN_PERCENT]:
                self.snowfallProbabilityInPercent = values[ForecastFields.SNOWFALL_PROBABILITY_IN_PERCENT]

            if self.precipitationProbabilityInPercent < values[ForecastFields.PRECIPITATION_PROBABILITY_IN_PERCENT]:
                self.precipitationProbabilityInPercent = values[ForecastFields.PRECIPITATION_PROBABILITY_IN_PERCENT]
