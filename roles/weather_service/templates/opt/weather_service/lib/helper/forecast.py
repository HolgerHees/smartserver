from suntime import Sun, SunTimeException
from datetime import datetime, timedelta
import logging

class WeatherBlock():
    def __init__(self, start):
        self.start = start
        self.end = None

        self.sunshineDurationInMinutes= 0
        self.effectiveCloudCoverInOcta= 0
        self.precipitationType = -100
        self.thunderstormProbabilityInPercent= 0
        self.freezingRainProbabilityInPercent= 0
        self.hailProbabilityInPercent= 0
        self.snowfallProbabilityInPercent= 0
        self.precipitationProbabilityInPercent= 0
        self.precipitationAmountInMillimeter= 0
        self.airTemperatureInCelsius = -100
        self.feelsLikeTemperatureInCelsius = -100
        self.windSpeedInKilometerPerHour= 0
        self.windDirectionInDegree= 0

        self.minAirTemperatureInCelsius = None
        self.maxAirTemperatureInCelsius = None
        self.maxPrecipitationAmountInMillimeter = 0
        self.maxIsSnowing = False

        self.svg = None

    def to_dict(self):
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

    def getPrecipitationAmountInMillimeter(self):
        return self.precipitationAmountInMillimeter

    def setPrecipitationAmountInMillimeter(self, value):
        self.precipitationAmountInMillimeter = value
        self.maxPrecipitationAmountInMillimeter = value
        self.precipitationProbabilityInPercent = 100 if value > 0 else 0

    def apply( self, hourlyData ):
        self.sunshineDurationInMinutes += hourlyData['sunshineDurationInMinutes']
        self.precipitationAmountInMillimeter += hourlyData['precipitationAmountInMillimeter']

        if self.effectiveCloudCoverInOcta < hourlyData['effectiveCloudCoverInOcta']:
            self.effectiveCloudCoverInOcta = hourlyData['effectiveCloudCoverInOcta']

        if self.precipitationType < hourlyData['precipitationType']:
            self.precipitationType = hourlyData['precipitationType']

        if self.thunderstormProbabilityInPercent < hourlyData['thunderstormProbabilityInPercent']:
            self.thunderstormProbabilityInPercent = hourlyData['thunderstormProbabilityInPercent']

        if hourlyData['precipitationAmountInMillimeter'] > 0:
            if self.freezingRainProbabilityInPercent < hourlyData['freezingRainProbabilityInPercent']:
                self.freezingRainProbabilityInPercent = hourlyData['freezingRainProbabilityInPercent']

            if self.hailProbabilityInPercent < hourlyData['hailProbabilityInPercent']:
                self.hailProbabilityInPercent = hourlyData['hailProbabilityInPercent']

            if self.snowfallProbabilityInPercent < hourlyData['snowfallProbabilityInPercent']:
                self.snowfallProbabilityInPercent = hourlyData['snowfallProbabilityInPercent']

            if self.precipitationProbabilityInPercent < hourlyData['precipitationProbabilityInPercent']:
                self.precipitationProbabilityInPercent = hourlyData['precipitationProbabilityInPercent']

            if self.maxPrecipitationAmountInMillimeter is None or self.maxPrecipitationAmountInMillimeter <= hourlyData['precipitationAmountInMillimeter']:
                self.maxPrecipitationAmountInMillimeter = hourlyData['precipitationAmountInMillimeter']

            if self.checkRainProbability( hourlyData['precipitationProbabilityInPercent'], hourlyData['precipitationAmountInMillimeter'] ):
                _isSnowing = hourlyData['freezingRainProbabilityInPercent'] > 10 or hourlyData['hailProbabilityInPercent'] > 10 or hourlyData['snowfallProbabilityInPercent'] > 10
                if not self.maxIsSnowing or _isSnowing:
                    if _isSnowing:
                        self.maxIsSnowing = True

        if self.airTemperatureInCelsius < hourlyData['airTemperatureInCelsius']:
            self.airTemperatureInCelsius = hourlyData['airTemperatureInCelsius']

        if self.feelsLikeTemperatureInCelsius < hourlyData['feelsLikeTemperatureInCelsius']:
            self.feelsLikeTemperatureInCelsius = hourlyData['feelsLikeTemperatureInCelsius']

        if self.windSpeedInKilometerPerHour < hourlyData['windSpeedInKilometerPerHour']:
            self.windSpeedInKilometerPerHour = hourlyData['windSpeedInKilometerPerHour']
            self.windDirectionInDegree = hourlyData['windDirectionInDegree']

        if self.minAirTemperatureInCelsius is None or self.minAirTemperatureInCelsius > hourlyData['airTemperatureInCelsius']:
            self.minAirTemperatureInCelsius = hourlyData['airTemperatureInCelsius']

        if self.maxAirTemperatureInCelsius is None or self.maxAirTemperatureInCelsius < hourlyData['airTemperatureInCelsius']:
            self.maxAirTemperatureInCelsius = hourlyData['airTemperatureInCelsius']

    def checkRainProbability( self, precipitationProbabilityInPercent, precipitationAmountInMillimeter ):
        return ( precipitationProbabilityInPercent >= 30 and precipitationAmountInMillimeter > 0 ) or ( precipitationProbabilityInPercent >= 25 and precipitationAmountInMillimeter > 0.5 )

class WeatherHelper():
    sunConfig = {
        'day': [ 'day', 'cloudy-day-0', 'cloudy-day-1', 'cloudy-day-2', 'cloudy' ],
        'night': [ 'night', 'cloudy-night-0', 'cloudy-night-1', 'cloudy-night-2', 'cloudy' ]
    }

    @staticmethod
    def getSunriseAndSunset(latitude, longitude):
        sun = Sun(latitude, longitude)
        sunrise = sun.get_sunrise_time().astimezone().replace(tzinfo=None)
        sunset = sun.get_sunset_time().astimezone().replace(tzinfo=None)

        return [sunrise, sunset]

    @staticmethod
    def calculateSummary( dataList ):
        minTemperature = dataList[0]['airTemperatureInCelsius'];
        maxTemperature = dataList[0]['airTemperatureInCelsius'];
        maxWindSpeed = dataList[0]['windSpeedInKilometerPerHour'];
        sumSunshine = 0;
        sumRain = 0;

        for entry in dataList:
            if minTemperature > entry['airTemperatureInCelsius']:
                minTemperature = entry['airTemperatureInCelsius']
            if maxTemperature < entry['airTemperatureInCelsius']:
                maxTemperature = entry['airTemperatureInCelsius']
            if maxWindSpeed < entry['maxWindSpeedInKilometerPerHour']:
                maxWindSpeed = entry['maxWindSpeedInKilometerPerHour']

            sumSunshine += entry['sunshineDurationInMinutes']
            sumRain += entry['precipitationAmountInMillimeter']

        return [ minTemperature, maxTemperature, maxWindSpeed, sumSunshine, sumRain ]

    @staticmethod
    def convertOctaToSVG(latitude, longitude, block):
        octa = block.effectiveCloudCoverInOcta
        #precipitationType = block.precipitationType

        starttime = block.start
        if block.end is None:
            timerange = 1
        else:
            timerange = int( ( block.end - block.start ).total_seconds() / 60 / 60 )

        sunrise, sunset = WeatherHelper.getSunriseAndSunset(latitude, longitude)

        cloudIndex = 0
        if block.effectiveCloudCoverInOcta >= 6:
            cloudIndex = 4
        elif block.effectiveCloudCoverInOcta >= 4.5:
            cloudIndex = 3
        elif block.effectiveCloudCoverInOcta >= 3.0:
            cloudIndex = 2
        elif block.effectiveCloudCoverInOcta >= 1.5:
            cloudIndex = 1

        minutes_to_add = ( timerange / 2 * 60)
        now = datetime.now()
        ref_datetime = starttime + timedelta(minutes=minutes_to_add)
        ref_datetime = ref_datetime.replace(year=now.year,month=now.month,day=now.day)
        isNight = ( ref_datetime < sunrise or ref_datetime > sunset )

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
