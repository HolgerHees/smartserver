from suntime import Sun, SunTimeException
from datetime import datetime, timedelta
import logging

class WeatherBlock():
    def __init__(self, start):
        self.start = start
        self.end = None
        self.sunshineDurationInMinutesSum = 0
        self.precipitationAmountInMillimeterSum= 0
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
        self.windSpeedInKilometerPerHour= 0
        self.windDirectionInDegree= 0

        self.minAirTemperatureInCelsius = None
        self.maxAirTemperatureInCelsius = None

        self.svg = None

    def to_json(self):
        return self.__dict__

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

    def apply( self, hourlyData ):
        self.sunshineDurationInMinutes += hourlyData['sunshineDurationInMinutes']
        self.precipitationAmountInMillimeter += hourlyData['precipitationAmountInMillimeter']

        if self.minAirTemperatureInCelsius is None or self.minAirTemperatureInCelsius > hourlyData['airTemperatureInCelsius']:
            self.minAirTemperatureInCelsius = hourlyData['airTemperatureInCelsius']

        if self.maxAirTemperatureInCelsius is None or self.maxAirTemperatureInCelsius < hourlyData['airTemperatureInCelsius']:
            self.maxAirTemperatureInCelsius = hourlyData['airTemperatureInCelsius']

        if self.effectiveCloudCoverInOcta < hourlyData['effectiveCloudCoverInOcta']:
            self.effectiveCloudCoverInOcta = hourlyData['effectiveCloudCoverInOcta']

        if self.precipitationType < hourlyData['precipitationType']:
            self.precipitationType = hourlyData['precipitationType']

        if self.thunderstormProbabilityInPercent < hourlyData['thunderstormProbabilityInPercent']:
            self.thunderstormProbabilityInPercent = hourlyData['thunderstormProbabilityInPercent']

        if self.freezingRainProbabilityInPercent < hourlyData['freezingRainProbabilityInPercent']:
            self.freezingRainProbabilityInPercent = hourlyData['freezingRainProbabilityInPercent']

        if self.hailProbabilityInPercent < hourlyData['hailProbabilityInPercent']:
            self.hailProbabilityInPercent = hourlyData['hailProbabilityInPercent']

        if self.snowfallProbabilityInPercent < hourlyData['snowfallProbabilityInPercent']:
            self.snowfallProbabilityInPercent = hourlyData['snowfallProbabilityInPercent']

        if self.precipitationProbabilityInPercent < hourlyData['precipitationProbabilityInPercent'] and self.precipitationAmountInMillimeter > 0:
            self.precipitationProbabilityInPercent = hourlyData['precipitationProbabilityInPercent']

        if self.airTemperatureInCelsius < hourlyData['airTemperatureInCelsius']:
            self.airTemperatureInCelsius = hourlyData['airTemperatureInCelsius']

        if self.windSpeedInKilometerPerHour < hourlyData['windSpeedInKilometerPerHour']:
            self.windSpeedInKilometerPerHour = hourlyData['windSpeedInKilometerPerHour']
            self.windDirectionInDegree = hourlyData['windDirectionInDegree']

class WeatherHelper():
    sunConfig = {
        'day': [ 'day', 'cloudy-day-0', 'cloudy-day-1', 'cloudy-day-2', 'cloudy' ],
        'night': [ 'night', 'cloudy-night-0', 'cloudy-night-1', 'cloudy-night-2', 'cloudy' ]
    }

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

        sun = Sun(latitude, longitude)
        sunrise = sun.get_sunrise_time().astimezone().replace(tzinfo=None)
        sunset = sun.get_sunset_time().astimezone().replace(tzinfo=None)

        index = 0
        if block.effectiveCloudCoverInOcta >= 6:
            index = 4
        elif block.effectiveCloudCoverInOcta >= 4.5:
            index = 3
        elif block.effectiveCloudCoverInOcta >= 3.0:
            index = 2
        elif block.effectiveCloudCoverInOcta >= 1.5:
            index = 1

        minutes_to_add = ( timerange / 2 * 60)
        now = datetime.now()
        ref_datetime = starttime + timedelta(minutes=minutes_to_add)
        ref_datetime = ref_datetime.replace(year=now.year,month=now.month,day=now.day)
        isNight = ( ref_datetime < sunrise or ref_datetime > sunset )

        icon = WeatherHelper.sunConfig[ 'night' if isNight else 'day' ][index];

        if block.precipitationProbabilityInPercent >= 30 and block.precipitationAmountInMillimeter > 0:
            if timerange == 24:
                if block.precipitationAmountInMillimeter >= 4:
                    amount = 4
                elif block.precipitationAmountInMillimeter >= 2:
                    amount = 3
                elif block.precipitationAmountInMillimeter >= 1:
                    amount = 2
                else:
                    amount = 1

            elif timerange >= 3:
                if block.precipitationAmountInMillimeter >= 3:
                    amount = 4
                elif block.precipitationAmountInMillimeter >= 2:
                    amount = 3
                elif block.precipitationAmountInMillimeter >= 1:
                    amount = 2
                else:
                    amount = 1

            else:
                if block.precipitationAmountInMillimeter >= 1.3:
                    amount = 4
                elif block.precipitationAmountInMillimeter >= 0.9:
                    amount = 3
                elif block.precipitationAmountInMillimeter >= 0.5:
                    amount = 2
                else:
                    amount = 1

            rain_type = 'snowflake' if ( block.freezingRainProbabilityInPercent >= 10 or block.hailProbabilityInPercent >= 10 or block.snowfallProbabilityInPercent >= 10 ) else 'raindrop'
            rain_type = "{}{}".format(rain_type, amount)
        else:
            rain_type = 'none'

        if block.thunderstormProbabilityInPercent >= 5:
            thunder_type = "thunder"
        else:
            thunder_type = 'none'

        return "{}_{}_{}_grayscaled.svg".format(icon, rain_type, thunder_type)
