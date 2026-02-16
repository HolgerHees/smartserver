from suntime import Sun, SunTimeException
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

        self.effectiveCloudCoverInOcta= 0

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
        self.minEffectiveCloudCoverInOcta = None
        self.maxEffectiveCloudCoverInOcta = None
        self.maxPrecipitationAmountInMillimeter = None
        self.maxIsSnowing = False

        self.svg = None

    def toDict(self):
        result = {}
        for key, value in self.__dict__.items():
            if key in ["start", "end"]:
                result[key] = value.isoformat()
            else:
                result[key] = value
        return result

    def setStart(self, start):
        self.start = start

    def getStart(self):
        return self.start

    def setEnd(self, end):
        self.end = end

    def setSVG(self, svg):
        self.svg = svg

    def setEffectiveCloudCover(self, value):
        self.effectiveCloudCoverInOcta = value

    def setPrecipitationAmountInMillimeter(self, value):
        self.precipitationAmountInMillimeter = value
        self.maxPrecipitationAmountInMillimeter = value
        self.precipitationProbabilityInPercent = 100 if value > 0 else 0

    def apply( self, hourlyData ):
        self.sunshineDurationInMinutes += hourlyData[ForecastFields.SUNSHINE_DURATION_IN_MINUTES]
        self.precipitationAmountInMillimeter += hourlyData[ForecastFields.PRECIPITATION_AMOUNT_IN_MILLIMETER]

        if self.airTemperatureInCelsius < hourlyData[ForecastFields.AIR_TEMPERATURE_IN_CELSIUS]:
            self.airTemperatureInCelsius = hourlyData[ForecastFields.AIR_TEMPERATURE_IN_CELSIUS]

        if self.minAirTemperatureInCelsius is None or self.minAirTemperatureInCelsius > hourlyData[ForecastFields.AIR_TEMPERATURE_IN_CELSIUS]:
            self.minAirTemperatureInCelsius = hourlyData[ForecastFields.AIR_TEMPERATURE_IN_CELSIUS]

        if self.maxAirTemperatureInCelsius is None or self.maxAirTemperatureInCelsius < hourlyData[ForecastFields.AIR_TEMPERATURE_IN_CELSIUS]:
            self.maxAirTemperatureInCelsius = hourlyData[ForecastFields.AIR_TEMPERATURE_IN_CELSIUS]

        if self.feelsLikeTemperatureInCelsius < hourlyData[ForecastFields.FEELS_LIKE_TEMPERATURE_IN_CELSIUS]:
            self.feelsLikeTemperatureInCelsius = hourlyData[ForecastFields.FEELS_LIKE_TEMPERATURE_IN_CELSIUS]

        if self.effectiveCloudCoverInOcta < hourlyData[ForecastFields.CLOUD_COVER_IN_OCTA]:
            self.effectiveCloudCoverInOcta = hourlyData[ForecastFields.CLOUD_COVER_IN_OCTA]

        if self.minEffectiveCloudCoverInOcta is None or self.minEffectiveCloudCoverInOcta > hourlyData[ForecastFields.CLOUD_COVER_IN_OCTA]:
            self.minEffectiveCloudCoverInOcta = hourlyData[ForecastFields.CLOUD_COVER_IN_OCTA]

        if self.maxEffectiveCloudCoverInOcta is None or self.maxEffectiveCloudCoverInOcta < hourlyData[ForecastFields.CLOUD_COVER_IN_OCTA]:
            self.maxEffectiveCloudCoverInOcta = hourlyData[ForecastFields.CLOUD_COVER_IN_OCTA]

        if self.windSpeedInKilometerPerHour < hourlyData[ForecastFields.WIND_SPEED_IN_KILOMETER_PER_HOUR]:
            self.windSpeedInKilometerPerHour = hourlyData[ForecastFields.WIND_SPEED_IN_KILOMETER_PER_HOUR]
            self.windDirectionInDegree = hourlyData[ForecastFields.WIND_DIRECTION_IN_DEGREE]

        if self.weatherCode < hourlyData[ForecastFields.WEATHER_CODE]:
            self.weatherCode = hourlyData[ForecastFields.WEATHER_CODE]

        if self.thunderstormProbabilityInPercent < hourlyData[ForecastFields.THUNDERSTORM_PROBABILITY_IN_PERCENT]:
            self.thunderstormProbabilityInPercent = hourlyData[ForecastFields.THUNDERSTORM_PROBABILITY_IN_PERCENT]

        if hourlyData[ForecastFields.PRECIPITATION_AMOUNT_IN_MILLIMETER] > 0:
            if self.freezingRainProbabilityInPercent < hourlyData[ForecastFields.FREEZING_RAIN_PROBABILITY_IN_PERCENT]:
                self.freezingRainProbabilityInPercent = hourlyData[ForecastFields.FREEZING_RAIN_PROBABILITY_IN_PERCENT]

            if self.hailProbabilityInPercent < hourlyData[ForecastFields.HAIL_PROBABILITY_IN_PERCENT]:
                self.hailProbabilityInPercent = hourlyData[ForecastFields.HAIL_PROBABILITY_IN_PERCENT]

            if self.snowfallProbabilityInPercent < hourlyData[ForecastFields.SNOWFALL_PROBABILITY_IN_PERCENT]:
                self.snowfallProbabilityInPercent = hourlyData[ForecastFields.SNOWFALL_PROBABILITY_IN_PERCENT]

            if self.precipitationProbabilityInPercent < hourlyData[ForecastFields.PRECIPITATION_PROBABILITY_IN_PERCENT]:
                self.precipitationProbabilityInPercent = hourlyData[ForecastFields.PRECIPITATION_PROBABILITY_IN_PERCENT]

            if self.maxPrecipitationAmountInMillimeter is None or self.maxPrecipitationAmountInMillimeter <= hourlyData[ForecastFields.PRECIPITATION_AMOUNT_IN_MILLIMETER]:
                self.maxPrecipitationAmountInMillimeter = hourlyData[ForecastFields.PRECIPITATION_AMOUNT_IN_MILLIMETER]

            if self.checkRainProbability( hourlyData[ForecastFields.PRECIPITATION_PROBABILITY_IN_PERCENT], hourlyData[ForecastFields.PRECIPITATION_AMOUNT_IN_MILLIMETER] ):
                _isSnowing = hourlyData[ForecastFields.FREEZING_RAIN_PROBABILITY_IN_PERCENT] > 10 or hourlyData[ForecastFields.HAIL_PROBABILITY_IN_PERCENT] > 10 or hourlyData[ForecastFields.SNOWFALL_PROBABILITY_IN_PERCENT] > 10
                if not self.maxIsSnowing or _isSnowing:
                    if _isSnowing:
                        self.maxIsSnowing = True

    def checkRainProbability( self, precipitationProbabilityInPercent, precipitationAmountInMillimeter ):
        return ( precipitationProbabilityInPercent >= 30 and precipitationAmountInMillimeter > 0 ) or ( precipitationProbabilityInPercent >= 25 and precipitationAmountInMillimeter > 0.5 )

class WeatherHelper():
    sunConfig = {
        'day': [ 'day', 'cloudy-day-0', 'cloudy-day-1', 'cloudy-day-2', 'cloudy' ],
        'night': [ 'night', 'cloudy-night-0', 'cloudy-night-1', 'cloudy-night-2', 'cloudy' ]
    }

    @staticmethod
    def getSunriseAndSunset(latitude, longitude, ref_datetime):
        #_ref_datetime = ref_datetime.replace(hour=0, minute=0, second=0)
        sun = Sun(latitude, longitude)
        sunrise = sun.get_sunrise_time(ref_datetime, time_zone=datetime.now().astimezone().tzinfo).replace(tzinfo=None, year=ref_datetime.year, month=ref_datetime.month, day=ref_datetime.day)
        sunset = sun.get_sunset_time(ref_datetime, time_zone=datetime.now().astimezone().tzinfo).replace(tzinfo=None, year=ref_datetime.year, month=ref_datetime.month, day=ref_datetime.day)

        return [sunrise, sunset]

    @staticmethod
    def calculateSummary( dataList ):
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
            if maxWindSpeed < entry[ForecastFields.WIND_GUST_IN_KILOMETER_PER_HOUR]:
                maxWindSpeed = entry[ForecastFields.WIND_GUST_IN_KILOMETER_PER_HOUR]

            sumSunshine += entry[ForecastFields.SUNSHINE_DURATION_IN_MINUTES]
            sumRain += entry[ForecastFields.PRECIPITATION_AMOUNT_IN_MILLIMETER]

        return [ minTemperature, maxTemperature, maxWindSpeed, sumSunshine, sumRain ]

    @staticmethod
    def convertOctaToSVG(latitude, longitude, block):
        return WeatherHelper._convertOctaToSVG(latitude, longitude, block, block.effectiveCloudCoverInOcta)

    @staticmethod
    def _convertOctaToSVG(latitude, longitude, block, cloud_cover):
        starttime = block.start
        timerange = int( ( block.end - block.start ).total_seconds() / 60 )

        ref_datetime = starttime + timedelta(minutes=timerange / 2)

        sunrise, sunset = WeatherHelper.getSunriseAndSunset(latitude, longitude, ref_datetime)

        isNight = ( ref_datetime < sunrise or ref_datetime > sunset )

        sun = Sun(latitude, longitude)
        #logging.info("     convertOctaToSVG: isNight: {} - ref_datetime: {} - sunrise: {} - sunset: {}".format(isNight, ref_datetime, sunrise, sunset ))

        cloudIndex = 0
        if cloud_cover >= 6:
            cloudIndex = 4
        elif cloud_cover >= 4.5:
            cloudIndex = 3
        elif cloud_cover >= 3.0:
            cloudIndex = 2
        elif cloud_cover >= 1.5:
            cloudIndex = 1

        if block.checkRainProbability( block.precipitationProbabilityInPercent, block.maxPrecipitationAmountInMillimeter ):
            if block.maxPrecipitationAmountInMillimeter >= 1.3:
                amount = 4
            elif block.maxPrecipitationAmountInMillimeter >= 0.9:
                amount = 3
            elif block.maxPrecipitationAmountInMillimeter >= 0.5:
                amount = 2
            else:
                amount = 1

            rain_type = 'snowflake' if block.maxIsSnowing else 'raindrop'
            #rain_type = 'snowflake' if ( block.freezingRainProbabilityInPercent >= 10 or block.hailProbabilityInPercent >= 10 or block.snowfallProbabilityInPercent >= 10 ) else 'raindrop'
            rain_type = "{}{}".format(rain_type, amount)
        else:
            rain_type = 'none'

        if block.thunderstormProbabilityInPercent >= 15:
            thunder_type = "thunder"
        else:
            thunder_type = 'none'

        if cloudIndex == 0 and ( rain_type != "none" or thunder_type != "none" ):
            cloudIndex = 1

        icon = WeatherHelper.sunConfig[ 'night' if isNight else 'day' ][cloudIndex];

        return "{}_{}_{}_grayscaled.svg".format(icon, rain_type, thunder_type)
