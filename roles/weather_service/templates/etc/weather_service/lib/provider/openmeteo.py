from datetime import datetime, timedelta
from pytz import timezone
import time
import logging

import requests
import urllib.parse
import json
import decimal

from lib.provider.provider import Provider

# possible alternative => https://open-meteo.com/

is_test = True

current_url  = "https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&timezone={timezone}&current={fields}"
current_config = {
    "airTemperatureInCelsius": "temperature_2m",
    "feelsLikeTemperatureInCelsius": "apparent_temperature",
    "relativeHumidityInPercent": "relativehumidity_2m",
    "windSpeedInKilometerPerHour": "windspeed_10m",
    "windDirectionInDegree": "winddirection_10m",
    "effectiveCloudCoverInOcta": [ [ "cloudcover" ], lambda self, fetched_values: self.buildEffectiveCloudCoverInOcta(fetched_values) ]
}

forecast_url = "https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&timezone={timezone}&forecast_days=14&past_days=0&hourly={fields}";
forecast_config = {
    "airTemperatureInCelsius": "temperature_2m",
    "feelsLikeTemperatureInCelsius": "apparent_temperature",
    "relativeHumidityInPercent": "relativehumidity_2m",
    "windSpeedInKilometerPerHour": "windspeed_10m",
    "windDirectionInDegree": "winddirection_10m",
    "effectiveCloudCoverInOcta": [ [ "cloudcover" ], lambda self, fetched_values: self.buildEffectiveCloudCoverInOcta(fetched_values) ],

    "thunderstormProbabilityInPercent": [ [ "cape" ], lambda self, fetched_values: self.buildThunderstormInPersent(fetched_values) ],

    "freezingRainProbabilityInPercent": [ [ "weathercode", "precipitation_probability" ], lambda self, fetched_values: self.buildFreezingRainInPercent(fetched_values) ],
    "hailProbabilityInPercent": [ [ "weathercode", "precipitation_probability" ], lambda self, fetched_values: self.buildHailInPercent(fetched_values) ],
    "snowfallProbabilityInPercent": [ [ "snowfall", "precipitation_probability" ], lambda self, fetched_values: self.buildSnowfallInPercent(fetched_values) ],

    "precipitationAmountInMillimeter": "precipitation",
    "precipitationProbabilityInPercent": [ [ "precipitation_probability" ], lambda self, fetched_values: self.buildPrecipitationInPersent(fetched_values) ],

    # https://www.nodc.noaa.gov/archive/arc0021/0002199/1.1/data/0-data/HTML/WMO-CODE/WMO4677.HTM
    "precipitationType": "weathercode",

    #"sunshineDurationInMinutes" ?????????????????????????

    "maxWindSpeedInKilometerPerHour": "windgusts_10m"
}
    
class RequestDataException(Exception):
    pass

class CurrentDataException(RequestDataException):
    pass
  
class ForecastDataException(RequestDataException):
    pass

class Fetcher(object):
    def __init__(self, config):
        self.config = config

    def get(self, url):
      
        headers = {}
        r = requests.get(url, headers=headers)
        if r.status_code != 200:
            raise RequestDataException("Failed getting data. Code: {}, Raeson: {}".format(r.status_code, r.reason))
        else:
            return json.loads(r.text)

    def buildEffectiveCloudCoverInOcta(self, fetched_values):
        return fetched_values["cloudcover"] * 9 / 100

    def buildThunderstormInPersent(self, fetched_values):
        # < 1000 Slight
        # 1000 – 2500 Moderate
        # 2500-3500 Very
        # > 3500 Extremely
        return int(round(fetched_values["cape"] * 100.0 / 3500.0, 0))
      
    # weather codes https://github.com/open-meteo/open-meteo/issues/287
    def buildFreezingRainInPercent(self, fetched_values):
        if fetched_values["weathercode"] not in [48,56,57,66,67]:
            return 0

        return self.buildPrecipitationInPersent(fetched_values)

    def buildHailInPercent(self, fetched_values):
        if fetched_values["weathercode"] not in [96,99]:
            return 0

        return self.buildPrecipitationInPersent(fetched_values)

    def buildSnowfallInPercent(self, fetched_values):
        if fetched_values["snowfall"] == 0:
            return 0

        return self.buildPrecipitationInPersent(fetched_values)

    def buildPrecipitationInPersent(self, fetched_values):
        if "precipitation_probability" in fetched_values and fetched_values["precipitation_probability"] is not None:
            return fetched_values["precipitation_probability"]
        #if fetched_values["rain"] > 10:
        #    return 100
        #if fetched_values["rain"] > 0:
        #    return 50
        return 0

    def collectFetchedFields(self, config):
        fields = []
        for mapping in config.values():
            if isinstance(mapping, str):
                fields.append(mapping)
            else:
                fields += mapping[0]
        return set(fields)

    def fetchCurrent(self, db, mqtt ):
        latitude, longitude = self.config.location.split(",")

        fields = self.collectFetchedFields(current_config)

        #"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current={fields}"
        url = current_url.format(latitude=latitude,longitude=longitude,timezone=self.config.timezone,fields=",".join(fields))
        data = self.get(url)
        if data == None or "current" not in data:
            raise ForecastDataException("Failed getting forecast data. Content: {}".format(data))

        current_fields = {}
        for messurementName, mapping in current_config.items():
            if isinstance(mapping, str):
                current_fields[messurementName] = data["current"][mapping]
            else:
                fetched_values = {}
                for field in mapping[0]:
                    fetched_values[field] = data["current"][field]
                current_fields[messurementName] = mapping[1](self,fetched_values)

        for field, value in current_fields.items():
            msg = "{}/weather/provider/current/{}".format(self.config.publish_topic,field)
            #logging.info("Publish: {} = {}".format(msg, value))
            mqtt.publish(msg, payload=value, qos=0, retain=False)

        observedFrom = datetime.now().astimezone().replace(minute=0, second=0,microsecond=0).strftime("%Y-%m-%dT%H:%M:%S%z")
        msg = "{}/weather/provider/current/refreshed".format(self.config.publish_topic)
        #logging.info("Publish: {} = {}".format(msg, observedFrom))
        mqtt.publish(msg, payload=observedFrom, qos=0, retain=False)

        logging.info("Current data published")

    def fetchForecast(self, mqtt ):
        latitude, longitude = self.config.location.split(",")

        fields = self.collectFetchedFields(forecast_config)

        #https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&hourly={fields}&forecast_days=14
        url = forecast_url.format(latitude=latitude,longitude=longitude,timezone=self.config.timezone,fields=",".join(fields))
        data = self.get(url)
        if data == None or "hourly" not in data:
            raise ForecastDataException("Failed getting forecast data. Content: {}".format(data))

        forecasts = {}
        for x, date_str in enumerate(data["hourly"]["time"]):
            validFrom = datetime.strptime(u"{0}".format(date_str),"%Y-%m-%dT%H:%M").astimezone()
            forecasts[validFrom.strftime("%Y-%m-%dT%H:%M:00%z")] = {"index": x}

        for messurementName, mapping in forecast_config.items():
            for period, forcastSlot in forecasts.items():
                if isinstance(mapping, str):
                    value = data["hourly"][mapping][forecasts[period]["index"]]
                    if value is None:
                        logging.info("{} {} is empty".format(messurementName, period))
                    forecasts[period][messurementName] = value
                else:
                    fetched_values = {}
                    for field in mapping[0]:
                        fetched_values[field] = data["hourly"][field][forecasts[period]["index"]]
                    forecasts[period][messurementName] = mapping[1](self,fetched_values)

        for period, forcastSlot in forecasts.items():
            date = period
            date = date.replace("+","plus")
            for field, value in forcastSlot.items():
                if field.startswith("index"):
                    continue
                msg = "{}/weather/provider/forecast/{}/{}".format(self.config.publish_topic,field,date)
                #logging.info("Publish: {} = {}".format(msg, value))
                mqtt.publish(msg, payload=value, qos=0, retain=False)
        msg = "{}/weather/provider/forecast/refreshed".format(self.config.publish_topic)
        #logging.info("Publish: {} = {}".format(msg, value))
        mqtt.publish(msg, payload="1", qos=0, retain=False)

        logging.info("Forecast data published • Total: {}".format(len(forecasts)))

class OpenMeteo(Provider):
    '''Handler client'''
    def __init__(self, config, db, mqtt):
        super().__init__(config, db, mqtt, "{}provider_openmeteo.json".format(config.lib_path))

    def _createFetcher(self, config):
        return Fetcher(config)
