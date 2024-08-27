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
    "windSpeedInKilometerPerHour": "windSpeedInKilometerPerHour",
    "maxWindSpeedInKilometerPerHour": "maxWindGustInKilometerPerHour", # => !!!!!!

    "effectiveCloudCoverInOcta": "effectiveCloudCoverInOcta",

    "precipitationAmountInMillimeter": "precipitationAmountInMillimeter",

#    "uvIndexWithClouds": "uvIndexWithClouds"
}

forecast_url = 'https://point-forecast.weather.mg/forecast/hourly?locatedAt={location}&validPeriod={period}&fields={fields}&validFrom={start}&validUntil={end}';
forecast_config = {
	'PT0S': [
		"airTemperatureInCelsius", 
		"feelsLikeTemperatureInCelsius", 
        "relativeHumidityInPercent",
		"windSpeedInKilometerPerHour", 
		"windDirectionInDegree", 
		"effectiveCloudCoverInOcta", 
		"thunderstormProbabilityInPercent",
		"freezingRainProbabilityInPercent",
		"hailProbabilityInPercent",
		"snowfallProbabilityInPercent",
		"precipitationProbabilityInPercent",
		# https://www.nodc.noaa.gov/archive/arc0021/0002199/1.1/data/0-data/HTML/WMO-CODE/WMO4677.HTM
		"precipitationType"
	],
	'PT1H': [
		"precipitationAmountInMillimeter", 
		"sunshineDurationInMinutes"
	],
	'PT3H': [
		"maxWindSpeedInKilometerPerHour"
	]
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
            raise RequestDataException("Failed getting data. Code: {}, Raeson: {}".format(r.status_code, r.text))
        else:
            return json.loads(r.text)
      
    def _prepareDate(self, date):
        date_str = date.strftime("%Y-%m-%dT%H:%M:%S%z")
        date_str = u"{0}:{1}".format(date_str[:-2],date_str[-2:])
        return date_str

    def fetchCurrent(self, db, mqtt ):
        
        #date = datetime.now().astimezone()#.now(timezone(self.config.timezone))
        #date = date.replace(minute=0, second=0,microsecond=0) + timedelta(hours=1)
        #end_date = self._prepareDate(date)
        
        #date = date - timedelta(hours=2)
        #start_date = self._prepareDate(date)
        
        latitude, longitude = self.config.location.split(",")
        location = u"{},{}".format(longitude,latitude)
        
        url = current_url.format(location=location, period="PT0S,PT1H,PT3H", fields=",".join(current_fields.values()))
        #url = current_url.format(location=location, period="PT0S,PT1H,PT3H", fields=",".join(current_fields.values()), start=urllib.parse.quote(start_date), end=urllib.parse.quote(end_date))
        #logging.info(url)

        currentFallbacks = None

        data = self.get(url)
        if "observations" not in data:
            raise CurrentDataException("Failed getting current data. Content: {}".format(data))

        #logging.info(url)
        #logging.info(data)

        data["observations"].reverse()
        _data = {"observation": {}, "missing_fields": current_fields.keys()}
        for observation in data["observations"]:
            #logging.info(observation)

            missing_fields = []
            for field in _data["missing_fields"]:
                if current_fields[field] in observation:
                    _data["observation"][current_fields[field]] = observation[current_fields[field]]
                else:
                    missing_fields.append(field)
            _data["missing_fields"] = missing_fields

            if len(_data["missing_fields"]) == 0:
                break

        for missing_field in list(_data["missing_fields"]):
            if currentFallbacks is None:
                with db.open() as db:
                    currentFallbacks = db.getOffset(0)

            if missing_field not in currentFallbacks:
                continue

            msg = "Use fallback data for field {}".format(missing_field)

            if missing_field == "effectiveCloudCoverInOcta" and ( datetime.now().hour >= 16 or datetime.now().hour <= 8 ):
                # can happen during night, because it is based in observed clouds from ground
                logging.info(msg)
            else:
                logging.warn(msg)

            _data["observation"][current_fields[missing_field]] = currentFallbacks[missing_field]
            _data["missing_fields"].remove(missing_field)

        #time.sleep(60000)

        if len(_data["missing_fields"]) > 0:
            raise CurrentDataException("Failed processing current data. Missing fields: {}, Content: {}".format(_data["missing_fields"], _data["observation"]))
        else:
            for field, _field in current_fields.items():
                mqtt.publish("{}/weather/provider/current/{}".format(self.config.publish_provider_topic,field), payload=_data["observation"][_field], qos=0, retain=False)

            #if "observedFrom" in _data["observation"]:
            #    observedFrom = _data["observation"]["observedFrom"]
            #    observedFrom = u"{0}{1}".format(observedFrom[:-3],observedFrom[-2:])
            #else:
            observedFrom = datetime.now().astimezone()
            observedFrom = observedFrom.replace(minute=0, second=0,microsecond=0)
            observedFrom = observedFrom.strftime("%Y-%m-%dT%H:%M:%S%z")

            #logging.info(observedFrom)
            mqtt.publish("{}/weather/provider/current/refreshed".format(self.config.publish_provider_topic), payload=observedFrom, qos=0, retain=False)

        logging.info("Current data published")

    def fetchForecast(self, mqtt ):
        date = datetime.now().astimezone()#.now(timezone(self.config.timezone))
        date = date.replace(minute=0, second=0,microsecond=0)

        #date = date.replace(hour=1, minute=0, second=0,microsecond=0)

        start_date = date + timedelta(hours=1)
        start_date_str = self._prepareDate(start_date)
        fetch_start_date_str = self._prepareDate(start_date - timedelta(hours=1)) # fetch on more hour
        
        latitude, longitude = self.config.location.split(",")
        location = u"{},{}".format(longitude,latitude)
        
        _entries = {}
        _periods = {}
        for period in forecast_config:
            fields = forecast_config[period]

            if period in ["PT0S", "PT1H"]:
                end_date = start_date + timedelta(hours=167)  # 7 days => 168 hours - 1 hour (because last one is excluded)
            elif period in ["PT3H"]:
                end_date = start_date + timedelta(hours=170) # 7 days => 167 hours + 3 hours, because of 3 hours timerange
            else:
                raise RequestDataException("Unhandled period")

            end_date_str = self._prepareDate(end_date)
            fetch_end_date_str = self._prepareDate(end_date + timedelta(hours=1)) # fetch on more hour

            url = forecast_url.format(location=location, period=period, fields=",".join(fields), start=urllib.parse.quote(fetch_start_date_str), end=urllib.parse.quote(fetch_end_date_str))
            #logging.info(url)

            data = self.get(url)
            if data == None or "forecasts" not in data:
                raise ForecastDataException("Failed getting forecast data. Content: {}".format(data))

            for forecast in data["forecasts"]:
                if "validFrom" not in forecast:
                    raise ForecastDataException("Missing forecast data. Content: {}".format(data))

            _periods[period] = {"start": start_date_str, "fetch_start":  fetch_start_date_str, "end": end_date_str, "fetch_end": fetch_end_date_str, "values": []}
            for forecast in data["forecasts"]:
                #logging.info(forecast)

                validFrom = datetime.strptime(u"{0}{1}".format(forecast["validFrom"][:-3],forecast["validFrom"][-2:]),"%Y-%m-%dT%H:%M:%S%z")
                validUntil = datetime.strptime(u"{0}{1}".format(forecast["validUntil"][:-3],forecast["validUntil"][-2:]),"%Y-%m-%dT%H:%M:%S%z")

                _periods[period]["values"].append({"from": forecast["validFrom"], "until": forecast["validUntil"]})

                if period == "PT0S":
                    # skip additional fetched hours
                    if validFrom < start_date or validUntil > end_date:
                        #logging.info("skip")
                        continue

                    values = {}
                    values["validFromAsString"] = u"{0}{1}".format(forecast["validFrom"][:-3],forecast["validFrom"][-2:])
                    values["validUntilAsString"] = u"{0}{1}".format(forecast["validUntil"][:-3],forecast["validUntil"][-2:])
                    values["validFromAsDatetime"] = validFrom
                    values["validUntilAsDatetime"] = validUntil
                    _entries[values["validFromAsString"]] = values

                    for field in fields:
                        values[field] = forecast[field]
                else:
                    #logging.info("{}: {} {}".format(period, forecast["validFrom"], forecast["validUntil"]))
                    for entry in _entries.values():
                        if entry["validFromAsDatetime"] >= validFrom and entry["validUntilAsDatetime"] < validUntil:
                            for field in fields:
                                entry[field] = forecast[field]

        _forecast_values = list(_entries.values())
        forecast_values = list(filter(lambda d: len(d) == 19, _forecast_values)) # 15 values + 4 datetime related fields

        if len(forecast_values) < 168:
            now = datetime.now()
            offset_in_seconds = abs(now.astimezone().utcoffset().total_seconds())
            midnight = now.replace(hour=0,minute=0,second=0,microsecond=0)
            from_time = midnight.time()
            to_time = (midnight + timedelta(seconds=offset_in_seconds)).time()

            # during midnight, there is a problem with missing values in the beginning
            if not ( now.time() >= from_time or now.time() <= to_time ):
                for period, data in _periods.items():
                    logging.info("PERIOD {}: {} => {}, FETCHED: {} => {}, COUNT: {}".format(period, data["start"], data["end"], data["fetch_start"], data["fetch_end"], len(data["values"])))
                    logging.info("DATA: {}".format(data["values"]))
                raise ForecastDataException("Not enough forecast data. Unvalidated: {}, Validated: {}".format(len(_forecast_values), len(forecast_values)))
            else:
                logging.warn("Not enough forecast data. Unvalidated: {}, Validated: {}".format(len(_forecast_values), len(forecast_values)))
        else:
            self.missing_data_count = 0

        for forecast in forecast_values:
            date = forecast["validFromAsString"]
            date = date.replace("+","plus")
            for field in forecast:
                if field.startswith("valid"):
                    continue
                mqtt.publish("{}/weather/provider/forecast/{}/{}".format(self.config.publish_provider_topic,field,date), payload=forecast[field], qos=0, retain=False)
            #mqtt.publish("{}/weather/forecast/refreshed/{}".format(self.config.publish_provider_topic,date), payload="1", qos=0, retain=False)
        mqtt.publish("{}/weather/provider/forecast/refreshed".format(self.config.publish_provider_topic), payload="1", qos=0, retain=False)

        logging.info("Forecast data published • Total: {}".format(len(forecast_values)))

class MeteoGroup(Provider):
    '''Handler client'''
    def __init__(self, config, db, mqtt):
        super().__init__(config, db, mqtt, "{}provider_meteogroup.json".format(config.lib_path))

    def _createFetcher(self, config):
        return Fetcher(config)
