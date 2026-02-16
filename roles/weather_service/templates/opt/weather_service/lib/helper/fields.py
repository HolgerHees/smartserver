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

    RAIN_PROBABILITY_IN_PERCENT = "rainProbabilityInPercent"
    RAIN_AMOUNT_IN_MILLIMETER = "rainAmountInMillimeter"

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

    RAIN_PROBABILITY_IN_PERCENT = "rainProbabilityInPercent"
    RAIN_AMOUNT_IN_MILLIMETER = "rainAmountInMillimeter"

    UV_INDEX = "uvIndex"

    SUNSHINE_DURATION_IN_MINUTES = "sunshineDurationInMinutes"

    # --------------------------
    CLOUDS_AS_SVG = "cloudsAsSVG"
    DEW_POINT_IN_CELSIUS = "dewpointInCelsius"
    PRESSURE_IN_HECTOPASCAL = "pressureInHectopascals"
    RAIN_DAILY_IN_MILLIMETER = "rainDailyInMillimeter"
    RAIN_RATE_IN_MILLIMETER_PER_HOUR = "rainRateInMillimeterPerHour"
    RAIN_LEVEL = "rainLevel"
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

    CurrentFields.RAIN_AMOUNT_IN_MILLIMETER:         ForecastFields.RAIN_AMOUNT_IN_MILLIMETER,
    CurrentFields.UV_INDEX:                          ForecastFields.UV_INDEX
}

StationFieldToCurrentFieldMappings = {
    "cloudCoverInOcta": CurrentFields.CLOUD_COVER_IN_OCTA,
    "rainLevel": CurrentFields.RAIN_LEVEL,
    "rainDailyInMillimeter": CurrentFields.RAIN_DAILY_IN_MILLIMETER,
    "rainLastHourInMillimeter": CurrentFields.RAIN_AMOUNT_IN_MILLIMETER,
    "rainRateInMillimeterPerHour": CurrentFields.RAIN_RATE_IN_MILLIMETER_PER_HOUR,
    "windDirectionInDegree": CurrentFields.WIND_DIRECTION_IN_DEGREE,
    "windSpeedInKilometerPerHour": CurrentFields.WIND_SPEED_IN_KILOMETER_PER_HOUR,
    "windGustInKilometerPerHour": CurrentFields.WIND_GUST_IN_KILOMETER_PER_HOUR,
    "dewpointInCelsius": CurrentFields.DEW_POINT_IN_CELSIUS,
    "airTemperatureInCelsius": CurrentFields.AIR_TEMPERATURE_IN_CELSIUS,
    "airHumidityInPercent": CurrentFields.RELATIVE_HUMIDITY_IN_PERCENT,
    "perceivedTemperatureInCelsius": CurrentFields.FEELS_LIKE_TEMPERATURE_IN_CELSIUS,
    "pressureInHectopascals": CurrentFields.PRESSURE_IN_HECTOPASCAL,
    "solarRadiationInWatt": CurrentFields.SOLAR_RADIATION_IN_WATT,
    "lightLevelInLux": CurrentFields.LIGHT_LEVEL_IN_LUX,
    "uvIndex": CurrentFields.UV_INDEX
}
