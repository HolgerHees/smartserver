from datetime import datetime, timedelta
import logging

from lib.helper.fields import ForecastFields


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

    def initCloudIcons(self, sunrise, sunset, getCloudSVGCallback, withSubIcons ):
        icons = []

        start = self.hourlyData[0][0]
        end = self.hourlyData[-1][0]

        timerange = int( ( end - start ).total_seconds() / 60 )
        ref_date = start + timedelta(minutes=timerange / 2)

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

        if withSubIcons:
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
