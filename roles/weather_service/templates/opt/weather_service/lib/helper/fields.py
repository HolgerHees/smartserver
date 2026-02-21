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

    WEATHER_CODE = "weatherCode"
    UV_INDEX = "uvIndex"

    DIRECT_RADIATION_IN_WATT = "directRadiationInWatt"
    DIFFUSE_RADIATION_IN_WATT = "diffuseRadiationInWatt"

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

# *** WEATHER CODES ***
# https://www.nodc.noaa.gov/archive/arc0021/0002199/1.1/data/0-data/HTML/WMO-CODE/WMO4677.HTM
# 00 — Bewölkungsentwicklung nicht beobachtet
# 01 — Bewölkung abnehmend
# 02 — Bewölkung unverändert
# 03 — Bewölkung zunehmend
# Dunst, Rauch, Staub oder Sand
# 04 — Sicht durch Rauch oder Asche vermindert
# 05 — trockener Dunst (relative Feuchte < 80 %)
# 06 — verbreiteter Schwebstaub, nicht vom Wind herangeführt
# 07 — Staub oder Sand bzw. Gischt, vom Wind herangeführt
# 08 — gut entwickelte Staub- oder Sandwirbel
# 09 — Staub- oder Sandsturm im Gesichtskreis, aber nicht an der Station
# Trockenereignisse
# 10 — feuchter Dunst (relative Feuchte > 80 %)
# 11 — Schwaden von Bodennebel
# 12 — durchgehender Bodennebel
# 13 — Wetterleuchten sichtbar, kein Donner gehört
# 14 — Niederschlag im Gesichtskreis, nicht den Boden erreichend
# 15 — Niederschlag in der Ferne (> 5 km), aber nicht an der Station
# 16 — Niederschlag in der Nähe (< 5 km), aber nicht an der Station
# 17 — Gewitter (Donner hörbar), aber kein Niederschlag an der Station
# 18 — Markante Böen im Gesichtskreis, aber kein Niederschlag an der Station
# 19 — Tromben (trichterförmige Wolkenschläuche) im Gesichtskreis
# Ereignisse der letzten Stunde, aber nicht zur Beobachtungszeit
# 20 — nach Sprühregen oder Schneegriesel
# 21 — nach Regen
# 22 — nach Schneefall
# 23 — nach Schneeregen oder Eiskörnern
# 24 — nach gefrierendem Regen
# 25 — nach Regenschauer
# 26 — nach Schneeschauer
# 27 — nach Graupel- oder Hagelschauer
# 28 — nach Nebel
# 29 — nach Gewitter
# Staubsturm, Sandsturm, Schneefegen oder -treiben
# 30 — leichter oder mäßiger Sandsturm, an Intensität abnehmend
# 31 — leichter oder mäßiger Sandsturm, unveränderte Intensität
# 32 — leichter oder mäßiger Sandsturm, an Intensität zunehmend
# 33 — schwerer Sandsturm, an Intensität abnehmend
# 34 — schwerer Sandsturm, unveränderte Intensität
# 35 — schwerer Sandsturm, an Intensität zunehmend
# 36 — leichtes oder mäßiges Schneefegen, unter Augenhöhe
# 37 — starkes Schneefegen, unter Augenhöhe
# 38 — leichtes oder mäßiges Schneetreiben, über Augenhöhe
# 39 — starkes Schneetreiben, über Augenhöhe
# Nebel oder Eisnebel
# 40 — Nebel in einiger Entfernung
# 41 — Nebel in Schwaden oder Bänken
# 42 — Nebel, Himmel erkennbar, dünner werdend
# 43 — Nebel, Himmel nicht erkennbar, dünner werdend
# 44 — Nebel, Himmel erkennbar, unverändert
# 45 — Nebel, Himmel nicht erkennbar, unverändert
# 46 — Nebel, Himmel erkennbar, dichter werdend
# 47 — Nebel, Himmel nicht erkennbar, dichter werdend
# 48 — Nebel mit Reifansatz, Himmel erkennbar
# 49 — Nebel mit Reifansatz, Himmel nicht erkennbar
# Sprühregen
# 50 — unterbrochener leichter Sprühregen
# 51 — durchgehend leichter Sprühregen
# 52 — unterbrochener mäßiger Sprühregen
# 53 — durchgehend mäßiger Sprühregen
# 54 — unterbrochener starker Sprühregen
# 55 — durchgehend starker Sprühregen
# 56 — leichter gefrierender Sprühregen
# 57 — mäßiger oder starker gefrierender Sprühregen
# 58 — leichter Sprühregen mit Regen
# 59 — mäßiger oder starker Sprühregen mit Regen
# Regen
# 60 — unterbrochener leichter Regen oder einzelne Regentropfen
# 61 — durchgehend leichter Regen
# 62 — unterbrochener mäßiger Regen
# 63 — durchgehend mäßiger Regen
# 64 — unterbrochener starker Regen
# 65 — durchgehend starker Regen
# 66 — leichter gefrierender Regen
# 67 — mäßiger oder starker gefrierender Regen
# 68 — leichter Schneeregen
# 69 — mäßiger oder starker Schneeregen
# Schnee
# 70 — unterbrochener leichter Schneefall oder einzelne Schneeflocken
# 71 — durchgehend leichter Schneefall
# 72 — unterbrochener mäßiger Schneefall
# 73 — durchgehend mäßiger Schneefall
# 74 — unterbrochener starker Schneefall
# 75 — durchgehend starker Schneefall
# 76 — Eisnadeln (Polarschnee)
# 77 — Schneegriesel
# 78 — Schneekristalle
# 79 — Eiskörner (gefrorene Regentropfen)
# Schauer
# 80 — leichter Regenschauer
# 81 — mäßiger oder starker Regenschauer
# 82 — äußerst heftiger Regenschauer
# 83 — leichter Schneeregenschauer
# 84 — mäßiger oder starker Schneeregenschauer
# 85 — leichter Schneeschauer
# 86 — mäßiger oder starker Schneeschauer
# 87 — leichter Graupelschauer
# 88 — mäßiger oder starker Graupelschauer
# 89 — leichter Hagelschauer
# 90 — mäßiger oder starker Hagelschauer
# Gewitter
# 91 — Gewitter in der letzten Stunde, zurzeit leichter Regen
# 92 — Gewitter in der letzten Stunde, zurzeit mäßiger oder starker Regen
# 93 — Gewitter in der letzten Stunde, zurzeit leichter Schneefall/Schneeregen/Graupel/Hagel
# 94 — Gewitter in der letzten Stunde, zurzeit mäßiger oder starker Schneefall/Schneeregen/Graupel/Hagel
# 95 — leichtes oder mäßiges Gewitter mit Regen oder Schnee
# 96 — leichtes oder mäßiges Gewitter mit Graupel oder Hagel
# 97 — starkes Gewitter mit Regen oder Schnee
# 98 — starkes Gewitter mit Sandsturm
# 99 — starkes Gewitter mit Graupel oder Hagel
