from datetime import datetime, timedelta
from pytz import timezone
import time
import logging

import requests
import urllib.parse
import json
import decimal

from lib.provider.provider import Provider, AuthException, RequestDataException, CurrentDataException, ForecastDataException

# https://api.weather.mg/

token_url    = "https://auth.weather.mg/oauth/token"

current_url  = 'https://point-observation.weather.mg/observation/hourly?locatedAt={location}&observedPeriod={period}&fields={fields}';
#current_url  = 'https://point-observation.weather.mg/observation/hourly?locatedAt={location}&observedPeriod={period}&fields={fields}&observedFrom={start}&observedUntil={end}';
current_fields = {
    "airTemperatureInCelsius": "airTemperatureInCelsius",
    "feelsLikeTemperatureInCelsius": "feelsLikeTemperatureInCelsius",
    "relativeHumidityInPercent": "relativeHumidityInPercent",

    "windDirectionInDegree": "windDirectionInDegree",
    "windSpeedInKilometerPerHour": [ ["windSpeedInMeterPerSecond"], lambda self, fetched_values: round(fetched_values["windSpeedInMeterPerSecond"] / 1000.0 * 60 * 60, 2) ],
    "maxWindSpeedInKilometerPerHour": [ ["maxWindGustInMeterPerSecond"], lambda self, fetched_values: round(fetched_values["maxWindGustInMeterPerSecond"] / 1000.0 * 60 * 60, 2) ],

    "effectiveCloudCoverInOcta": "effectiveCloudCoverInOcta",

	# https://www.nodc.noaa.gov/archive/arc0021/0002199/1.1/data/0-data/HTML/WMO-CODE/WMO4677.HTM
    "weatherCode": "weatherCodeTraditional",

    "precipitationAmountInMillimeter": "precipitationAmountInMillimeter",
	"sunshineDurationInMinutes": "sunshineDurationInMinutes"
}

forecast_url = 'https://point-forecast.weather.mg/forecast/hourly?locatedAt={location}&validPeriod={period}&fields={fields}&validFrom={start}&validUntil={end}';
forecast_config = {
    "airTemperatureInCelsius": "airTemperatureInCelsius",
    "feelsLikeTemperatureInCelsius": "feelsLikeTemperatureInCelsius",
    "relativeHumidityInPercent": "relativeHumidityInPercent",

    "windDirectionInDegree": "windDirectionInDegree",
    "windSpeedInKilometerPerHour": [ ["windSpeedInMeterPerSecond"], lambda self, fetched_values: round(fetched_values["windSpeedInMeterPerSecond"] / 1000.0 * 60 * 60, 2) ],
	"maxWindSpeedInKilometerPerHour": [ ["maxWindGustInMeterPerSecond"], lambda self, fetched_values: round(fetched_values["maxWindGustInMeterPerSecond"] / 1000.0 * 60 * 60, 2) ],

    "effectiveCloudCoverInOcta": "effectiveCloudCoverInOcta",

    "thunderstormProbabilityInPercent": "thunderstormProbabilityInPercent",
    "freezingRainProbabilityInPercent": "freezingRainProbabilityInPercent",
    "hailProbabilityInPercent": "hailProbabilityInPercent",
    "snowfallProbabilityInPercent": "snowfallProbabilityInPercent",

    "precipitationProbabilityInPercent": "precipitationProbabilityInPercent",
	"precipitationAmountInMillimeter": "precipitationAmountInMillimeter",

    # https://www.nodc.noaa.gov/archive/arc0021/0002199/1.1/data/0-data/HTML/WMO-CODE/WMO4677.HTM
    "weatherCode": "weatherCodeTraditional",
    "uvIndexWithClouds": "uvIndexWithClouds",

	"sunshineDurationInMinutes": "sunshineDurationInMinutes"
}
    
class Fetcher(object):
    def __init__(self, config):
        self.config = config

        self.auth = self.getAuth()

    def getAuth(self):
      
        fields = {'grant_type': 'client_credentials'};
      
        r = requests.post(token_url, data=fields, auth=(self.config.api_username, self.config.api_password))
        if r.status_code != 200:
            raise AuthException("Failed getting auth token. Code: {}, Raeson: {}".format(r.status_code, r.text))
        else:
            data = json.loads(r.text)
            if "access_token" in data:
                return data["access_token"]
            
        raise AuthException("Failed getting auth token. Content: {}".format(r.text))
      
    def get(self, url):
      
        headers = {"Authorization": "Bearer {}".format(self.auth)}
        r = requests.get(url, headers=headers)
        if r.status_code != 200:
            raise RequestDataException("Failed getting data. Code: {}, Reason: {}, Url: {}".format(r.status_code, r.text, url))
        else:
            return json.loads(r.text)
      
    def _prepareDate(self, date):
        date_str = date.strftime("%Y-%m-%dT%H:%M:%S%z")
        date_str = u"{0}:{1}".format(date_str[:-2],date_str[-2:])
        return date_str

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
        location = u"{},{}".format(longitude,latitude)

        fields = self.collectFetchedFields(current_fields)
        
        url = current_url.format(location=location, period="PT0S,PT1H,PT3H", fields=",".join(fields))
        #logging.info(url)

        currentFallbacks = None

        data = self.get(url)
        if "observations" not in data:
            raise CurrentDataException("Failed getting current data. Content: {}, Url: {}".format(data, url))

        data["observations"].reverse()
        #_data = {"observation": {}, "missing_fields": list(fields)}
        current_data = {}
        for observation in data["observations"]:
            for k, v in observation.items():
                if k not in current_data:
                    current_data[k] = v

        current = {}
        for messurementName, mapping in current_fields.items():
            if isinstance(mapping, str):
                if mapping not in current_data:
                    continue

                value = current_data[mapping]
                if value is None:
                    logging.info("{} {} is empty".format(messurementName, period))
            else:
                fetched_values = {}
                for field in mapping[0]:
                    if field not in current_data:
                        continue
                    fetched_values[field] = current_data[field]

                if len(mapping[0]) != len(fetched_values):
                    continue

                value = mapping[1](self,fetched_values)
            current[messurementName] = value

        result = []
        for field, value in current.items():
            result.append({"field": field, "value": value })

        return result

    def fetchForecast(self, mqtt):
        date = datetime.now().astimezone()#.now(timezone(self.config.timezone))
        date = date.replace(minute=0, second=0,microsecond=0)

        #date = date.replace(hour=1, minute=0, second=0,microsecond=0)

        start_date = date + timedelta(hours=1)
        start_date_str = self._prepareDate(start_date)
        fetch_start_date_str = self._prepareDate(start_date - timedelta(hours=1)) # fetch on more hour
        
        latitude, longitude = self.config.location.split(",")
        location = u"{},{}".format(longitude,latitude)

        fields = self.collectFetchedFields(forecast_config)

        end_date = start_date + timedelta(hours=170)
        end_date_str = self._prepareDate(end_date)
        fetch_end_date_str = self._prepareDate(end_date + timedelta(hours=1)) # fetch on more hour

        url = forecast_url.format(location=location, period="PT0S,PT1H,PT3H", fields=",".join(fields), start=urllib.parse.quote(fetch_start_date_str), end=urllib.parse.quote(fetch_end_date_str))
        data = self.get(url)

        if data == None or "forecasts" not in data:
            raise ForecastDataException("Failed getting forecast data. Content: {}".format(data))

        forecast_ptxx = []
        forecast_pt0s = []
        for slot in data["forecasts"]:
            if "validFrom" not in slot:
                raise ForecastDataException("Missing forecast data. Content: {}".format(data))

            validFrom = datetime.strptime(u"{0}{1}".format(slot["validFrom"][:-3],slot["validFrom"][-2:]),"%Y-%m-%dT%H:%M:%S%z")
            validUntil = datetime.strptime(u"{0}{1}".format(slot["validUntil"][:-3],slot["validUntil"][-2:]),"%Y-%m-%dT%H:%M:%S%z")
            slot["validFrom"] = validFrom

            if slot["validPeriod"] == "PT0S":
                slot["validUntil"] = validUntil + timedelta(hours=1)
                forecast_pt0s.append(slot)
            else:
                slot["validUntil"] = validUntil
                forecast_ptxx.append(slot)

            del slot["locatedAt"]
            del slot["validPeriod"]

        for slot_ptxx in forecast_ptxx:
             for slot_pt0s in forecast_pt0s:
                if slot_pt0s["validFrom"] < slot_ptxx["validUntil"] and slot_pt0s["validUntil"] > slot_ptxx["validFrom"]:
                    for k, v in slot_ptxx.items():
                        slot_pt0s[k] = v

        if len(forecast_pt0s[-1]) != len(fields) + 2:
            del forecast_pt0s[-1]

        forecasts = {}
        for x, forecast_data in enumerate(forecast_pt0s):
            forecasts[forecast_data["validFrom"].strftime("%Y-%m-%dT%H:%M:00%z")] = {"index": x, "validFrom": forecast_data["validFrom"]}

        for messurementName, mapping in forecast_config.items():
            for validFrom, forcastSlot in forecasts.items():
                if isinstance(mapping, str):
                    value = forecast_pt0s[forecasts[validFrom]["index"]][mapping]
                    if value is None:
                        logging.info("{} {} is empty".format(messurementName, validFrom))
                    forecasts[validFrom][messurementName] = value
                else:
                    fetched_values = {}
                    for field in mapping[0]:
                        fetched_values[field] = forecast_pt0s[forecasts[validFrom]["index"]][field]
                    forecasts[validFrom][messurementName] = mapping[1](self,fetched_values)

        result = []
        for validFrom, forcastSlot in forecasts.items():
            for field in forcastSlot:
                if field in ["index","validFrom"]:
                    continue
                result.append({"field": field, "timestamp": int(forcastSlot["validFrom"].timestamp()), "value": forcastSlot[field] })

        return result

class MeteoGroup(Provider):
    '''Handler client'''
    def __init__(self, config, db, mqtt):
        super().__init__(config, db, mqtt, "{}provider_meteogroup.json".format(config.lib_path))

    def _createFetcher(self, config):
        return Fetcher(config)
