class __EnumBaseType__(type):
    def __iter__(self):
        return iter(list([v for k, v in self.__dict__.items() if not k.startswith("__")]))

class ForecastFields(metaclass=__EnumBaseType__):
    AIR_TEMPERATURE_IN_CELSIUS = "airTemperatureInCelsius"
    FEELS_LIKE_TEMPERATURE_IN_CELSIUS = "feelsLikeTemperatureInCelsius"

    RELATIVE_HUMIDITY_IN_PERCENT = "relativeHumidityInPercent"

    WIND_DIRECTION_IN_DEGREE = "windDirectionInDegree"
    WIND_SPEED_IN_KILOMETER_PER_HOUR = "windSpeedInKilometerPerHour"
    WIND_GUST_IN_KILOMETER_PER_HOUR = "windGustInKilometerPerHour"

    CLOUD_COVER_IN_OCTA = "cloudCoverInOcta"

    PRECIPITATION_PROBABILITY_IN_PERCENT = "precipitationProbabilityInPercent"
    PRECIPITATION_AMOUNT_IN_MILLIMETER = "precipitationAmountInMillimeter"

    # https://www.nodc.noaa.gov/archive/arc0021/0002199/1.1/data/0-data/HTML/WMO-CODE/WMO4677.HTM
    WEATHER_CODE = "weatherCode"
    UV_INDEX = "uvIndex"

    SUNSHINE_DURATION_IN_MINUTES = "sunshineDurationInMinutes"

    # --------------------------
    THUNDERSTORM_PROBABILITY_IN_PERCENT = "thunderstormProbabilityInPercent"
    FREEZING_RAIN_PROBABILITY_IN_PERCENT = "freezingRainProbabilityInPercent"
    HAIL_PROBABILITY_IN_PERCENT = "hailProbabilityInPercent"
    SNOWFALL_PROBABILITY_IN_PERCENT = "snowfallProbabilityInPercent"

class CurrentFields(metaclass=__EnumBaseType__):
    AIR_TEMPERATURE_IN_CELSIUS = "airTemperatureInCelsius"
    FEELS_LIKE_TEMPERATURE_IN_CELSIUS = "feelsLikeTemperatureInCelsius"

    RELATIVE_HUMIDITY_IN_PERCENT = "relativeHumidityInPercent"

    WIND_DIRECTION_IN_DEGREE = "windDirectionInDegree"
    WIND_SPEED_IN_KILOMETER_PER_HOUR = "windSpeedInKilometerPerHour"
    WIND_GUST_IN_KILOMETER_PER_HOUR = "windGustInKilometerPerHour"

    CLOUD_COVER_IN_OCTA = "cloudCoverInOcta"

    PRECIPITATION_PROBABILITY_IN_PERCENT = "precipitationProbabilityInPercent"
    PRECIPITATION_AMOUNT_IN_MILLIMETER = "precipitationAmountInMillimeter"

    UV_INDEX = "uvIndex"

    SUNSHINE_DURATION_IN_MINUTES = "sunshineDurationInMinutes"

    # --------------------------
    CLOUDS_AS_SVG = "cloudsAsSVG"
    DEW_POINT_IN_CELSIUS = "dewpointInCelsius"
    PRESSURE_IN_HECTOPASCAL = "pressureInHectopascals"
    PRECIPITATION_DAILY_IN_MILLIMETER = "precipitationDailyInMillimeter"
    PRECIPITATION_RATE_IN_MILLIMETER_PER_HOUR = "precipitationRateInMillimeterPerHour"
    PRECIPITATION_LEVEL = "precipitationLevel"
    SOLAR_RADIATION_IN_WATT = "solarRadiationInWatt"
    LIGHT_LEVEL_IN_LUX = "lightLevelInLux"

CurrentFieldFallbackMappings = {
    CurrentFields.AIR_TEMPERATURE_IN_CELSIUS:        ForecastFields.AIR_TEMPERATURE_IN_CELSIUS,
    CurrentFields.FEELS_LIKE_TEMPERATURE_IN_CELSIUS: ForecastFields.FEELS_LIKE_TEMPERATURE_IN_CELSIUS,

    CurrentFields.RELATIVE_HUMIDITY_IN_PERCENT:      ForecastFields.RELATIVE_HUMIDITY_IN_PERCENT,

    CurrentFields.WIND_DIRECTION_IN_DEGREE:          ForecastFields.WIND_DIRECTION_IN_DEGREE,
    CurrentFields.WIND_SPEED_IN_KILOMETER_PER_HOUR:  ForecastFields.WIND_SPEED_IN_KILOMETER_PER_HOUR,
    CurrentFields.WIND_GUST_IN_KILOMETER_PER_HOUR:   ForecastFields.WIND_GUST_IN_KILOMETER_PER_HOUR,

    CurrentFields.CLOUD_COVER_IN_OCTA:               ForecastFields.CLOUD_COVER_IN_OCTA,

    #CurrentFields.PRECIPITATION_PROBABILITY_IN_PERCENT:       ForecastFields.PRECIPITATION_PROBABILITY_IN_PERCENT, # calculated
    CurrentFields.PRECIPITATION_AMOUNT_IN_MILLIMETER:         ForecastFields.PRECIPITATION_AMOUNT_IN_MILLIMETER,

    CurrentFields.UV_INDEX:                          ForecastFields.UV_INDEX

    #CurrentFields.SUNSHINE_DURATION_IN_MINUTES:      ForecastFields.SUNSHINE_DURATION_IN_MINUTES # calculated
}

StationFieldToCurrentFieldMappings = {
    "airTemperatureInCelsius": CurrentFields.AIR_TEMPERATURE_IN_CELSIUS,
    "feelsLikeTemperatureInCelsius": CurrentFields.FEELS_LIKE_TEMPERATURE_IN_CELSIUS,

    "relativeHumidityInPercent": CurrentFields.RELATIVE_HUMIDITY_IN_PERCENT,

    "windDirectionInDegree": CurrentFields.WIND_DIRECTION_IN_DEGREE,
    "windSpeedInKilometerPerHour": CurrentFields.WIND_SPEED_IN_KILOMETER_PER_HOUR,
    "windGustInKilometerPerHour": CurrentFields.WIND_GUST_IN_KILOMETER_PER_HOUR,

    "cloudCoverInOcta": CurrentFields.CLOUD_COVER_IN_OCTA,

    "precipitationAmountInMillimeter": CurrentFields.PRECIPITATION_AMOUNT_IN_MILLIMETER,

    "uvIndex": CurrentFields.UV_INDEX,

    "dewpointInCelsius": CurrentFields.DEW_POINT_IN_CELSIUS,
    "pressureInHectopascals": CurrentFields.PRESSURE_IN_HECTOPASCAL,
    "precipitationDailyInMillimeter": CurrentFields.PRECIPITATION_DAILY_IN_MILLIMETER,
    "precipitationRateInMillimeterPerHour": CurrentFields.PRECIPITATION_RATE_IN_MILLIMETER_PER_HOUR,
    "precipitationLevel": CurrentFields.PRECIPITATION_LEVEL,
    "solarRadiationInWatt": CurrentFields.SOLAR_RADIATION_IN_WATT,
    "lightLevelInLux": CurrentFields.LIGHT_LEVEL_IN_LUX
}
