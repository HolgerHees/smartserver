from datetime import datetime, timedelta
from pytz import timezone
import time
import logging

import requests
import urllib.parse
import json
import decimal

from lib.provider.provider import Provider, RequestDataException, CurrentDataException, ForecastDataException
from lib.helper.fields import ForecastFields

# possible alternative => https://open-meteo.com/
# weather codes https://github.com/open-meteo/open-meteo/issues/287

is_test = True

current_url  = "https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&timezone={timezone}&current={fields}"
current_config = {
    ForecastFields.AIR_TEMPERATURE_IN_CELSIUS: "temperature_2m",
    ForecastFields.FEELS_LIKE_TEMPERATURE_IN_CELSIUS: "apparent_temperature",
    ForecastFields.RELATIVE_HUMIDITY_IN_PERCENT: "relativehumidity_2m",

    ForecastFields.WIND_DIRECTION_IN_DEGREE: "winddirection_10m",
    ForecastFields.WIND_SPEED_IN_KILOMETER_PER_HOUR: "windspeed_10m",
    ForecastFields.WIND_GUST_IN_KILOMETER_PER_HOUR: "windgusts_10m",

    ForecastFields.CLOUD_COVER_IN_OCTA: [ [ "cloudcover" ], lambda self, fetched_values: fetched_values["cloudcover"] * 8 / 100 ],

    ForecastFields.WEATHER_CODE: "weathercode",

    ForecastFields.PRECIPITATION_AMOUNT_IN_MILLIMETER: "precipitation"
    #ForecastFields.SUNSHINE_DURATION_IN_MINUTES: [ [ "sunshine_duration" ], lambda self, fetched_values: int(round(fetched_values["sunshine_duration"] / 60,0)) ]
}

forecast_url = "https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&timezone={timezone}&forecast_days=14&past_days=0&hourly={fields}";
forecast_config = {
    ForecastFields.AIR_TEMPERATURE_IN_CELSIUS: "temperature_2m",
    ForecastFields.FEELS_LIKE_TEMPERATURE_IN_CELSIUS: "apparent_temperature",
    ForecastFields.RELATIVE_HUMIDITY_IN_PERCENT: "relativehumidity_2m",

    ForecastFields.WIND_DIRECTION_IN_DEGREE: "winddirection_10m",
    ForecastFields.WIND_SPEED_IN_KILOMETER_PER_HOUR: "windspeed_10m",
    ForecastFields.WIND_GUST_IN_KILOMETER_PER_HOUR: "windgusts_10m",

    ForecastFields.CLOUD_COVER_IN_OCTA: [ [ "cloudcover" ], lambda self, fetched_values: fetched_values["cloudcover"] * 8 / 100 ],

    ForecastFields.THUNDERSTORM_PROBABILITY_IN_PERCENT: [ [ "cape" ], lambda self, fetched_values: int(round(fetched_values["cape"] * 100.0 / 3500.0, 0)) ], # < 1000 Slight, 1000 – 2500 Moderate, 2500-3500 Very, > 3500 Extremely
    ForecastFields.FREEZING_RAIN_PROBABILITY_IN_PERCENT: [ [ "weathercode", "precipitation_probability" ], lambda self, fetched_values: 0 if fetched_values["weathercode"] not in [48,56,57,66,67] else fetched_values["precipitation_probability"] ],
    ForecastFields.HAIL_PROBABILITY_IN_PERCENT: [ [ "weathercode", "precipitation_probability" ], lambda self, fetched_values: 0 if fetched_values["weathercode"] not in [96,99] else fetched_values["precipitation_probability"] ],
    ForecastFields.SNOWFALL_PROBABILITY_IN_PERCENT: [ [ "snowfall", "precipitation_probability" ], lambda self, fetched_values: 0 if fetched_values["snowfall"] == 0 else fetched_values["precipitation_probability"] ],

    ForecastFields.PRECIPITATION_AMOUNT_IN_MILLIMETER: "precipitation",
    ForecastFields.PRECIPITATION_PROBABILITY_IN_PERCENT: "precipitation_probability",

    # https://www.nodc.noaa.gov/archive/arc0021/0002199/1.1/data/0-data/HTML/WMO-CODE/WMO4677.HTM
    ForecastFields.WEATHER_CODE: "weathercode",
    ForecastFields.UV_INDEX: "uv_index",

    ForecastFields.SUNSHINE_DURATION_IN_MINUTES: [ [ "sunshine_duration" ], lambda self, fetched_values: int(round(fetched_values["sunshine_duration"] / 60,0)) ]
}
    
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

    def collectFetchedFields(self, config):
        fields = []
        for mapping in config.values():
            if isinstance(mapping, str):
                fields.append(mapping)
            else:
                fields += mapping[0]
        return set(fields)

    def fetchCurrent(self, mqtt):
        latitude, longitude = self.config.location.split(",")

        fields = self.collectFetchedFields(current_config)

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

        result = []
        for field, value in current_fields.items():
            result.append({"field": field, "value": value })
        return result

    def fetchForecast(self, mqtt):
        latitude, longitude = self.config.location.split(",")

        fields = self.collectFetchedFields(forecast_config)

        url = forecast_url.format(latitude=latitude,longitude=longitude,timezone=self.config.timezone,fields=",".join(fields))
        data = self.get(url)
        if data == None or "hourly" not in data or "minutely_15" not in data:
            raise ForecastDataException("Failed getting forecast data. Content: {}".format(data))

        forecasts = {}
        for x, date_str in enumerate(data["hourly"]["time"]):
            validFrom = datetime.strptime(u"{0}".format(date_str),"%Y-%m-%dT%H:%M").astimezone()
            forecasts[validFrom.strftime("%Y-%m-%dT%H:%M:00%z")] = {"index": x, "validFrom": validFrom}

        for messurementName, mapping in forecast_config.items():
            for validFrom, forcastSlot in forecasts.items():
                if isinstance(mapping, str):
                    value = data["hourly"][mapping][forecasts[validFrom]["index"]]
                    if value is None:
                        logging.info("{} {} is empty".format(messurementName, validFrom))
                    forecasts[validFrom][messurementName] = value
                else:
                    fetched_values = {}
                    for field in mapping[0]:
                        fetched_values[field] = data["hourly"][field][forecasts[validFrom]["index"]]
                    forecasts[validFrom][messurementName] = mapping[1](self,fetched_values)

        result = []
        for validFrom, forcastSlot in forecasts.items():
            for field, value in forcastSlot.items():
                if field.startswith("index", "validFrom"):
                    continue
                result.append({"field": field, "timestamp": int(forcastSlot["validFrom"].timestamp()), "value": value })
        return result

class OpenMeteo(Provider):
    '''Handler client'''
    def __init__(self, config, db, mqtt):
        super().__init__(config, db, mqtt, "{}provider_openmeteo.json".format(config.lib_path))

    def _createFetcher(self, config):
        return Fetcher(config)
