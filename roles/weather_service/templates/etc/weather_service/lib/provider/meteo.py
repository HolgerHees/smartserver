import traceback

from datetime import datetime, timedelta
from pytz import timezone
import time
import threading
import logging

import requests
import urllib.parse
import json
import decimal

from lib.db import DBException


token_url    = "https://auth.weather.mg/oauth/token"
current_url  = 'https://point-observation.weather.mg/search?locatedAt={location}&observedPeriod={period}&fields={fields}&observedFrom={start}&observedUntil={end}';
current_fields = [
    "airTemperatureInCelsius", 
    "feelsLikeTemperatureInCelsius",
    "relativeHumidityInPercent",
    "windSpeedInKilometerPerHour",
    "windDirectionInDegree",
    "effectiveCloudCoverInOcta"
]

forecast_url = 'https://point-forecast.weather.mg/search?locatedAt={location}&validPeriod={period}&fields={fields}&validFrom={start}&validUntil={end}';
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
    
summeryOffsets = [0,4,8]
summeryFields = ["airTemperatureInCelsius","effectiveCloudCoverInOcta"]

class AuthException(Exception):
    pass

class RequestDataException(Exception):
    pass

class CurrentDataException(RequestDataException):
    pass
  
class ForecastDataException(RequestDataException):
    pass

class Fetcher(object):
    def __init__(self, config):
        self.config = config

    def getAuth(self):
      
        fields = {'grant_type': 'client_credentials'};
      
        r = requests.post(token_url, data=fields, auth=(self.config.api_username, self.config.api_password))
        if r.status_code != 200:
            raise AuthException("Failed getting auth token. Code: {}, Raeson: {}".format(r.status_code, r.reason))
        else:
            data = json.loads(r.text)
            if "access_token" in data:
                return data["access_token"]
            
        raise AuthException("Failed getting auth token. Content: {}".format(r.text))
      
    def get(self, url, token):
      
        headers = {"Authorization": "Bearer {}".format(token)}
        r = requests.get(url, headers=headers)
        if r.status_code != 200:
            raise RequestDataException("Failed getting data. Code: {}, Raeson: {}".format(r.status_code, r.reason))
        else:
            return json.loads(r.text)
      
    def fetchCurrent(self, token, mqtt, currentFallbacks ):
        
        date = datetime.now(timezone(self.config.timezone))
        end_date = date.strftime("%Y-%m-%dT%H:%M:%S%z")
        end_date = u"{0}:{1}".format(end_date[:-2],end_date[-2:])
        
        date = date - timedelta(hours=2)
        start_date = date.strftime("%Y-%m-%dT%H:%M:%S%z")
        start_date = u"{0}:{1}".format(start_date[:-2],start_date[-2:])
        
        latitude, longitude = self.config.location.split(",")
        location = u"{},{}".format(longitude,latitude)
        
        url = current_url.format(location=location, period="PT0S", fields=",".join(current_fields), start=urllib.parse.quote(start_date), end=urllib.parse.quote(end_date))
        
        data = self.get(url,token)
        if "observations" not in data:
            raise CurrentDataException("Failed getting current data. Content: {}".format(data))
        else:
            data["observations"].reverse()
            observedFrom = None
            missing_fields = None

            _data = {"observation": None, "missing_fields": current_fields}
            for observation in data["observations"]:
                missing_fields = [field for field in current_fields if field not in observation]

                if _data["observation"] is None or len(_data["missing_fields"]) < len(missing_fields):
                    _data["observation"] = observation
                    _data["missing_fields"] = missing_fields

                if len(_data["missing_fields"]) == 0:
                    break

            for missing_field in list(_data["missing_fields"]):
                if missing_field not in currentFallbacks:
                    continue

                logging.info("Use fallback data for field {}".format(missing_field))

                _data["observation"][missing_field] = currentFallbacks[missing_field]
                _data["missing_fields"].remove(missing_field)


            #time.sleep(60000)

            if len(_data["missing_fields"]) > 0:
                raise CurrentDataException("Failed processing current data. Missing fields: {}, Content: {}".format(_data["missing_fields"], _data["observation"]))
            else:
                for field in current_fields:
                    mqtt.publish("{}/weather/provider/current/{}".format(self.config.publish_topic,field), payload=_data["observation"][field], qos=0, retain=False)
                observedFrom = _data["observation"]["observedFrom"]

                mqtt.publish("{}/weather/provider/current/refreshed".format(self.config.publish_topic), payload=observedFrom, qos=0, retain=False)

            logging.info("Current data published")
            
    def fetchForecast(self, token, mqtt ):
        date = datetime.now(timezone(self.config.timezone))
        start_date = date.strftime("%Y-%m-%dT%H:%M:%S%z")
        start_date = u"{0}:{1}".format(start_date[:-2],start_date[-2:])
        
        date = date + timedelta(hours=169) # 7 days + 1 hour
        end_date = date.strftime("%Y-%m-%dT%H:%M:%S%z")
        end_date = u"{0}:{1}".format(end_date[:-2],end_date[-2:])

        latitude, longitude = self.config.location.split(",")
        location = u"{},{}".format(longitude,latitude)
        
        currentFallbacks = None
        entries = {}
        for period in forecast_config:
            fields = forecast_config[period]
            url = forecast_url.format(location=location, period=period, fields=",".join(fields), start=urllib.parse.quote(start_date), end=urllib.parse.quote(end_date))
                   
            data = self.get(url,token)
            if data == None or "forecasts" not in data:
                raise ForecastDataException("Failed getting forecast data. Content: {}".format(data))
              
            for forecast in data["forecasts"]:
                key = forecast["validFrom"]
                if key not in entries:
                    values = {} 
                    values["validFrom"] = forecast["validFrom"]
                    entries[key] = values
                else:
                    values = entries[key];
                    
                for field in fields:
                    values[field] = forecast[field]

            if period == "PT0S":
                currentFallbacks = values
                
        sets = []
        for key in sorted(entries.keys()):
            sets.append(entries[key])
            
        for field in forecast_config["PT3H"]:
            value = None
            for values in sets:
                if field in values:
                    value = values[field]
                elif value != None:
                    values[field] = value
                else:
                    raise ForecastDataException("Missing PT3H value")
          
        sets = list(filter(lambda d: len(d) == 16, sets))
        
        if len(sets) < 168:
            raise ForecastDataException("Not enough forecast data. Count: {}".format(len(sets)))

        for forecast in sets:
            date = forecast["validFrom"]
            forecast.pop("validFrom") 
            date = date.replace("+","plus")
            for field in forecast:
                mqtt.publish("{}/weather/provider/forecast/{}/{}".format(self.config.publish_topic,field,date), payload=forecast[field], qos=0, retain=False)
            #mqtt.publish("{}/weather/forecast/refreshed/{}".format(self.config.publish_topic,date), payload="1", qos=0, retain=False)
        mqtt.publish("{}/weather/provider/forecast/refreshed".format(self.config.publish_topic), payload="1", qos=0, retain=False)

        logging.info("Forecast data published • Total: {}".format(len(sets)))

        return currentFallbacks

    def triggerSummerizedItems(self, db, mqtt):
        with db.open() as db:
            result = db.getFullDay()

            tmp = {}
            for field in summeryFields:
                tmp[field] = [ None, None, decimal.Decimal(0.0) ]
            for row in result:
                for field in tmp:
                    value = row[field]
                    if tmp[field][0] == None:
                        tmp[field][0] = decimal.Decimal(0.0) + value
                        tmp[field][1] = decimal.Decimal(0.0) + value
                    else:
                        if tmp[field][0] > value:
                            tmp[field][0] = value
                        if tmp[field][1] < value:
                            tmp[field][1] = value

                    tmp[field][2] = tmp[field][2] + value
            for field in summeryFields:
                tmp[field][2] = tmp[field][2] / len(result)

                mqtt.publish("{}/weather/provider/items/{}/{}".format(self.config.publish_topic,field,"min"), payload=str(tmp[field][0]).encode("utf-8"), qos=0, retain=False)
                mqtt.publish("{}/weather/provider/items/{}/{}".format(self.config.publish_topic,field,"max"), payload=str(tmp[field][1]).encode("utf-8"), qos=0, retain=False)
                mqtt.publish("{}/weather/provider/items/{}/{}".format(self.config.publish_topic,field,"avg"), payload=str(tmp[field][2]).encode("utf-8"), qos=0, retain=False)

            for offset in summeryOffsets:
                data = db.getOffset(offset)
                for field, value in data.items():
                    mqtt.publish("{}/weather/provider/items/{}/{}".format(self.config.publish_topic,field,offset), payload=str(value).encode("utf-8"), qos=0, retain=False)
            mqtt.publish("{}/weather/provider/items/refreshed".format(self.config.publish_topic), payload="1", qos=0, retain=False)

            logging.info("Summery data published")

class Meteo(threading.Thread):
    '''Handler client'''
    def __init__(self, config, db, mqtt):
        threading.Thread.__init__(self)

        self.is_running = True

        self.config = config
        self.db = db
        self.mqtt = mqtt

        self.event = threading.Event()

        self.service_metrics = { "data_provider": -1, "data_current": -1, "data_forecast": -1, "publish": -1 }

        self.last_consume_error = None

    def run(self):
        #status = os.fdopen(self.dhcpListenerProcess.stdout.fileno())
        #status = os.fdopen(os.dup(self.dhcpListenerProcess.stdout.fileno()))
        if not self.config.publish_topic or not self.config.api_username or not self.config.api_password:
            logging.info("Publishing disabled")
            return
        
        error_count = 0
        while self.is_running:
            try:
                fetcher = Fetcher(self.config)

                authToken = fetcher.getAuth()

                currentFallbacks = fetcher.fetchForecast(authToken,self.mqtt)
                self.service_metrics["data_forecast"] = 1

                fetcher.fetchCurrent(authToken,self.mqtt, currentFallbacks)
                self.service_metrics["data_current"] = 1

                fetcher.triggerSummerizedItems(self.db, self.mqtt)
                
                date = datetime.now(timezone(self.config.timezone))
                target = date.replace(minute=5,second=0)
                
                if target <= date:
                    target = target + timedelta(hours=1)

                diff = target - date
                
                sleepTime = diff.total_seconds()  
                
                error_count = 0

                self.service_metrics["data_provider"] = 1
                self.service_metrics["publish"] = 1
            except ForecastDataException as e:
                logging.info("{}: {}".format(str(e.__class__),str(e)))
                self.service_metrics["data_forecast"] = 0
                error_count += 1
            except CurrentDataException as e:
                logging.info("{}: {}".format(str(e.__class__),str(e)))
                self.service_metrics["data_current"] = 0
                error_count += 1
            except (RequestDataException,AuthException,requests.exceptions.RequestException) as e:
                logging.info("{}: {}".format(str(e.__class__),str(e)))
                self.service_metrics["data_provider"] = 0
                error_count += 1
            except DBException:
                error_count += 1
            #except MQTT Exceptions?? as e:
            #    logging.info("{}: {}".format(str(e.__class__),str(e)))
            #    self.service_metrics["mqtt"] = 0
            #    error_count += 1
            except Exception as e:
                logging.info("{}: {}".format(str(e.__class__),str(e)))
                traceback.print_exc()
                self.service_metrics["publish"] = 0
                error_count += 1

            if error_count > 0:
                sleepTime = 600 * error_count if error_count < 6 else 3600

            logging.info("Sleep {} seconds".format(sleepTime))
            self.event.wait(sleepTime)
            self.event.clear()

            #requests.exceptions.ConnectionError, urllib3.exceptions.MaxRetryError, urllib3.exceptions.NewConnectionError

    def getStateMetrics(self):
        state_metrics = []

        for name, value in self.service_metrics.items():
            state_metrics.append("weather_service_state{{type=\"provider_{}\"}} {}".format(name,value))
        return state_metrics
            
    def terminate(self):
        self.is_running = False
        self.event.set()


