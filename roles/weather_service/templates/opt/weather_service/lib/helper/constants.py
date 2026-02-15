class ForecastFields():
    AIR_TEMPERATURE_IN_CELSIUS = "airTemperatureInCelsius"
    FEELS_LIKE_TEMPERATURE_IN_CELSIUS = "feelsLikeTemperatureInCelsius"
    RELATIVE_HUMIDITY_IN_PERCENT = "relativeHumidityInPercent"

    WIND_DIRECTION_IN_DEGREE = "windDirectionInDegree"
    WIND_SPEED_IN_KILOMETER_PER_HOUR = "windSpeedInKilometerPerHour"
    MAX_WIND_SPEED_IN_KILOMETER_PER_HOUR = "maxWindSpeedInKilometerPerHour"

    EFFECTVE_CLOUD_COVER_IN_OCTA = "effectiveCloudCoverInOcta"

    THUNDERSTORM_PROBAILITY_IN_PERCENT = "thunderstormProbabilityInPercent"
    FREEZING_RAIN_PROBAILITY_IN_PERCENT = "freezingRainProbabilityInPercent"
    HAIL_PROBAILITY_IN_PERCENT = "hailProbabilityInPercent"
    SNOWFALL_PROBAILITY_IN_PERCENT = "snowfallProbabilityInPercent"

    PERCIPITATION_PROBAILITY_IN_PERCENT = "precipitationProbabilityInPercent"
    PERCIPITATION_AMOUNT_IN_MILLIMETER = "precipitationAmountInMillimeter"

    # https://www.nodc.noaa.gov/archive/arc0021/0002199/1.1/data/0-data/HTML/WMO-CODE/WMO4677.HTM
    WEATHER_CODE = "weatherCode"
    UV_INDEX_WITH_CLOUDS = "uvIndexWithClouds"

    SUNSHINE_DURATION_IN_MINUTES = "sunshineDurationInMinutes"

class CurrentFields():
    SUNSHINE_DURATION_IN_MINUTES = "currentSunshineDurationInMinutes"
    RAIN_PROBABILITY_IN_PERCENT = "currentRainProbabilityInPercent"
    CLOUDS_AS_SVG = "currentCloudsAsSVG"

    AIR_TEMPERATURE_IN_CELSIUS = "currentAirTemperatureInCelsius"
    PERCEIVED_TEMPERATURE_IN_CELSIUS = "currentPerceivedTemperatureInCelsius"
    DEW_POINT_IN_CELSIUS = "currentDewpointInCelsius"

    AIR_HUMIDITY_IN_PERCENT = "currentAirHumidityInPercent"
    PRESSURE_IN_HECTOPASCAL = "currentPressureInHectopascals"

    WIND_DIRECTION_IN_DEGREE = "currentWindDirectionInDegree"
    WIND_SPEED_IN_KILOMETER_PER_HOUR = "currentWindSpeedInKilometerPerHour"
    WIND_GUST_IN_KILOMETER_PER_HOUR = "currentWindGustInKilometerPerHour"

    CLOUD_COVER_IN_OCTA = "currentCloudCoverInOcta"

    RAIN_LEVEL = "currentRainLevel"
    RAIN_DAILY_IN_MILLIMETER = "currentRainDailyInMillimeter"
    RAIN_LAST_HOUR_IN_MILLIMETER = "currentRainLastHourInMillimeter"
    RAIN_RATE_IN_MILLIMETER_PER_HOUR = "currentRainRateInMillimeterPerHour"

    SOLAR_RADIATION_IN_WATT = "currentSolarRadiationInWatt"
    LIGHT_LEVEL_IN_LUX = "currentLightLevelInLux"
    UV_INDEX = "currentUvIndex"
CurrentFieldsList = {k: v for k, v in CurrentFields.__dict__.items() if not k.startswith("__")}
