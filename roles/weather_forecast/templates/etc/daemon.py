import signal
import paho.mqtt.client as mqtt
import sys

import traceback

import MySQLdb

from datetime import datetime, timedelta
from pytz import timezone
import time

import requests
import urllib.parse
import json

import config

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

class MySQL(object):
    def getOffsetSQL(offset):
        return "SELECT * FROM {} WHERE `datetime` > DATE_ADD(NOW(), INTERVAL {} HOUR) ORDER BY `datetime` ASC LIMIT 1".format(config.db_table,offset-1)

    def getEntrySQL(timestamp):
        return u"SELECT * FROM {} WHERE `datetime`=from_unixtime({})".format(config.db_table,timestamp)
      
    def getUpdateSQL(timestamp,fields):
        return u"UPDATE {} SET {} WHERE `datetime`=from_unixtime({})".format(config.db_table,",".join(fields),timestamp)
    
    def getInsertUpdateSQL(timestamp,fields):
        insert_values = [ u"`datetime`=from_unixtime({})".format(timestamp) ]
        insert_values.extend(fields)
        return u"INSERT INTO {} SET {} ON DUPLICATE KEY UPDATE {}".format(config.db_table,",".join(insert_values),",".join(fields))
    
class Fetcher(object):
    def getAuth(self):
      
        fields = {'grant_type': 'client_credentials'};
      
        r = requests.post(token_url, data=fields, auth=(config.api_username, config.api_password))
        if r.status_code != 200:
            print("Failed getting auth token. Code: {}, Raeson: {}".format(r.status_code, r.reason), flush=True, file=sys.stderr)
        else:
            data = json.loads(r.text)
            if "access_token" in data:
                return data["access_token"]
            
            print("Failed getting auth token. Content: {}".format(r.text), flush=True, file=sys.stderr)
      
        return None
      
    def get(self, url, token):
      
        headers = {"Authorization": "Bearer {}".format(token)}
        r = requests.get(url, headers=headers)
        if r.status_code != 200:
            print("Failed getting data. Code: {}, Raeson: {}".format(r.status_code, r.reason), flush=True, file=sys.stderr)
            return None
        else:
            return json.loads(r.text)
      
    def fetchCurrent(self, token, mqtt_client ):
        
        date = datetime.now(timezone(config.timezone))
        end_date = date.strftime("%Y-%m-%dT%H:%M:%S%z")
        end_date = u"{0}:{1}".format(end_date[:-2],end_date[-2:])
        
        date = date - timedelta(hours=2)
        start_date = date.strftime("%Y-%m-%dT%H:%M:%S%z")
        start_date = u"{0}:{1}".format(start_date[:-2],start_date[-2:])
        
        latitude, longitude = config.location.split(",")
        location = u"{},{}".format(longitude,latitude)
        
        url = current_url.format(location=location, period="PT0S", fields=",".join(current_fields), start=urllib.parse.quote(start_date), end=urllib.parse.quote(end_date))
        
        data = self.get(url,token)
        if data == None or "observations" not in data:
            print("Failed getting current data. Content: {}".format(data), flush=True, file=sys.stderr)
        else:
            data["observations"].reverse()
            observedFrom = None
            for observation in data["observations"]:
                if len(observation) != 10:
                    continue
                  
                for field in current_fields:
                    mqtt_client.publish("{}/weather/current/{}".format(config.publish_topic,field), payload=observation[field], qos=0, retain=False)            
                observedFrom = observation["observedFrom"]
                break
          
            if observedFrom is None:
                print("Failed processing current data. Content: {}".format(data), flush=True, file=sys.stderr)
            else:
                mqtt_client.publish("{}/weather/current/refreshed".format(config.publish_topic), payload=observedFrom, qos=0, retain=False)            

            print("Current data published", flush=True)
            
    def fetchForecast(self, token, mqtt_client ):
        date = datetime.now(timezone(config.timezone))
        start_date = date.strftime("%Y-%m-%dT%H:%M:%S%z")
        start_date = u"{0}:{1}".format(start_date[:-2],start_date[-2:])
        
        date = date + timedelta(hours=169) # 7 days + 1 hour
        end_date = date.strftime("%Y-%m-%dT%H:%M:%S%z")
        end_date = u"{0}:{1}".format(end_date[:-2],end_date[-2:])

        latitude, longitude = config.location.split(",")
        location = u"{},{}".format(longitude,latitude)
        
        entries = {}
        for period in forecast_config:
            fields = forecast_config[period]
            url = forecast_url.format(location=location, period=period, fields=",".join(fields), start=urllib.parse.quote(start_date), end=urllib.parse.quote(end_date))
                   
            data = self.get(url,token)
            if data == None or "forecasts" not in data:
                print("Failed getting forecast data. Content: {}".format(data), flush=True, file=sys.stderr)
                continue
              
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
                
        sets = []
        for key in sorted(entries.keys()):
            sets.append(entries[key])
            
        for field in forecast_config["PT3H"]:
            value = None
            for values in sets:
                if field in values:
                    value = values[field]
                else:
                    values[field] = value
          
        sets = list(filter(lambda d: len(d) == 16, sets))
        
        if len(sets) < 168:
            print("Not enough forecast data. Count: {}".format(len(sets)), flush=True, file=sys.stderr)

        for forecast in sets:
            date = forecast["validFrom"]
            forecast.pop("validFrom") 
            date = date.replace("+","plus")
            for field in forecast:
                mqtt_client.publish("{}/weather/forecast/{}/{}".format(config.publish_topic,field,date), payload=forecast[field], qos=0, retain=False)  
            #mqtt_client.publish("{}/weather/forecast/refreshed/{}".format(config.publish_topic,date), payload="1", qos=0, retain=False)            
        mqtt_client.publish("{}/weather/forecast/refreshed".format(config.publish_topic), payload="1", qos=0, retain=False)            

        print("Forecast data published • Total: {}".format(len(sets)), flush=True)

    def triggerSummerizedItems(self, mqtt_client):
        db = MySQLdb.connect(host=config.db_host,user=config.db_username,passwd=config.db_password,db=config.db_name)
        cursor = db.cursor()
        
        for offset in summeryOffsets:            
            cursor.execute(MySQL.getOffsetSQL(offset))
            data = cursor.fetchone()
            
            fields = list(map(lambda x:x[0], cursor.description))
            
            for field in summeryFields:
                index = fields.index(field)
                mqtt_client.publish("{}/weather/items/{}/{}".format(config.publish_topic,field,offset), payload=str(data[index]).encode("utf-8"), qos=0, retain=False)
        mqtt_client.publish("{}/weather/items/refreshed".format(config.publish_topic), payload="1", qos=0, retain=False)    
            
        cursor.close()
        db.close()
            
        print("Summery data published", flush=True)

class Handler(object):
    '''Handler client'''
    def __init__(self):
        self.mqtt_client = None
        
        self.current_values = None
        self.forecast_values = None
        
    def connectMqtt(self):
        print("Connection to mqtt ...", end='', flush=True)
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = lambda client, userdata, flags, rc: self.on_connect(client, userdata, flags, rc)
        self.mqtt_client.on_disconnect = lambda client, userdata, rc: self.on_disconnect(client, userdata, rc)
        self.mqtt_client.on_message = lambda client, userdata, msg: self.on_message(client, userdata, msg) 
        self.mqtt_client.connect(config.mosquitto_host, 1883, 60)
        print(" initialized", flush=True)
        
        self.mqtt_client.loop_start()
        
    def loop(self):        
        #status = os.fdopen(self.dhcpListenerProcess.stdout.fileno())
        #status = os.fdopen(os.dup(self.dhcpListenerProcess.stdout.fileno()))
        
        while True:
            if config.publish_topic and config.api_username and config.api_password:
                fetcher = Fetcher()
                authToken = fetcher.getAuth()
                if authToken != None:
                    fetcher.fetchCurrent(authToken,self.mqtt_client)
                    fetcher.fetchForecast(authToken,self.mqtt_client)
                    fetcher.triggerSummerizedItems(self.mqtt_client)
            
            date = datetime.now(timezone(config.timezone))
            target = date.replace(minute=5,second=0)
            
            if target < date:
                target = target + timedelta(hours=1)

            diff = target - date

            print("Sleep {} seconds".format(diff.total_seconds()),flush=True)
            time.sleep(diff.total_seconds())
            

    def on_connect(self,client,userdata,flags,rc):
        print("Connected to mqtt with result code:"+str(rc), flush=True)
        client.subscribe('+/weather/#')
        
    def on_disconnect(self,client, userdata, rc):
        print("Disconnect from mqtt with result code:"+str(rc), flush=True)

    def on_message(self,client,userdata,msg):
        try:
            #print("Topic " + msg.topic + ", message:" + str(msg.payload), flush=True)
            topic = msg.topic.split("/")
            if topic[2] == u"current":
                if topic[3] == u"refreshed":
                    db = MySQLdb.connect(host=config.db_host,user=config.db_username,passwd=config.db_password,db=config.db_name)
                    cursor = db.cursor()

                    datetime_str = msg.payload.decode("utf-8") 
                    datetime_str = u"{0}{1}".format(datetime_str[:-3],datetime_str[-2:])
                    validFrom = datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M:%S%z')
                    
                    update_values = []
                    for field in self.current_values:
                        update_values.append("`{}`='{}'".format(field,self.current_values[field]))
                        
                    cursor.execute(MySQL.getEntrySQL(validFrom.timestamp()))
                    if cursor.rowcount == 1:
                        cursor.execute(MySQL.getUpdateSQL(validFrom.timestamp(),update_values))
                        db.commit()        
                        print(u"Current data processed • Updated {}".format( "yes" if cursor.rowcount != 0 else "no" ), flush=True)
                    else:
                        print(u"Current data not updated: Topic: " + msg.topic + ", message:" + str(msg.payload), flush=True, file=sys.stderr)
                        
                    self.current_values = None

                    cursor.close()
                    db.close()
                else:
                    if self.current_values is None:
                        self.current_values = {}
                    self.current_values[topic[3]] = msg.payload.decode("utf-8")
            elif topic[2] == u"forecast":
                if topic[3] == u"refreshed":
                    db = MySQLdb.connect(host=config.db_host,user=config.db_username,passwd=config.db_password,db=config.db_name)
                    cursor = db.cursor()
                    
                    updateCount = 0
                    insertCount = 0
                    for datetime_str in self.forecast_values:
                        validFrom = datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M:%S%z')

                        update_values = []
                        for field in self.forecast_values[datetime_str]:
                            update_values.append(u"`{}`='{}'".format(field,self.forecast_values[datetime_str][field]))
                            
                        cursor.execute(MySQL.getEntrySQL(validFrom.timestamp()))
                        isUpdate = True if cursor.rowcount == 1 else False
                      
                        cursor.execute(MySQL.getInsertUpdateSQL(validFrom.timestamp(),update_values))
                        
                        if cursor.rowcount > 0:
                            if isUpdate:
                                updateCount += 1
                            else:
                                insertCount += 1
                        db.commit()        
                        
                    print("Forcecasts processed • Total: {}, Updated: {}, Inserted: {}".format(len(self.forecast_values),updateCount,insertCount), flush=True)
                    
                    self.forecast_values = None

                    cursor.close()
                    db.close()
                else:
                    if self.forecast_values is None:
                        self.forecast_values = {}
                        
                    field = topic[3]
                    datetime_str = topic[4].replace("plus","+")
                    datetime_str = u"{0}{1}".format(datetime_str[:-3],datetime_str[-2:])
                    
                    if datetime_str not in self.forecast_values:
                        self.forecast_values[datetime_str] = {}
                        
                    self.forecast_values[datetime_str][field] = msg.payload.decode("utf-8")
            elif topic[2] == u"items":
                if topic[3] == u"refreshed":
                    print("Summery data processed", flush=True)
            else:
                print("Unknown topic " + msg.topic + ", message:" + str(msg.payload), flush=True, file=sys.stderr)
        except Exception as e:
            print("Exception: {}".format(str(e)))
            traceback.print_exc()
            
    def terminate(self):
        if self.mqtt_client != None:
            print("Close connection to mqtt", flush=True)
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
        
handler = Handler()
handler.connectMqtt()

def cleanup(signum, frame):
    #print(signum)
    #print(frame)
    handler.terminate()
    exit(0)

signal.signal(signal.SIGTERM, cleanup)
signal.signal(signal.SIGINT, cleanup)

handler.loop()
