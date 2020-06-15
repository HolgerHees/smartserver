from __future__ import print_function
from roomba import Roomba
import paho.mqtt.client as mqtt
import time
import json
import logging

#put your own values here
broker = 'localhost'    #ip of mqtt broker
user = 'user'           #mqtt username
password = 'password'   #mqtt password
#broker = None #if not using local mqtt broker

address = '{{roomba_ip}}'
blid = '{{vault_roomba_blid}}'
roombaPassword = '{{vault_roomba_password}}'

def broker_on_connect(client, userdata, flags, rc):
    print("Broker Connected with result code "+str(rc))
    #subscribe to roomba feedback
    if rc == 0:
        mqttc.subscribe(brokerCommand)
        mqttc.subscribe(brokerSetting)

def broker_on_message(mosq, obj, msg):
    #publish to roomba
    if "command" in msg.topic:
        print("Received COMMAND: %s" % msg.payload.decode("utf-8"))
        myroomba.send_command(msg.payload.decode("utf-8"))
    elif "setting" in msg.topic:
        print("Received SETTING: %s" % msg.payload.decode("utf-8"))
        cmd = msg.payload.decode("utf-8").split()
        myroomba.set_preference(cmd[0], cmd[1])

def broker_on_publish(mosq, obj, mid):
    pass

def broker_on_subscribe(mosq, obj, mid, granted_qos):
    print("Broker Subscribed: %s %s" % (str(mid), str(granted_qos)))

def broker_on_disconnect(mosq, obj, rc):
    print("Broker disconnected")

def broker_on_log(mosq, obj, level, string):
    print(string)


mqttc = None
if broker is not None:
    brokerCommand = "/roomba/command"
    brokerSetting = "/roomba/setting"
    brokerFeedback = "/roomba/feedback"

    #connect to broker
    mqttc = mqtt.Client()
    #Assign event callbacks
    mqttc.on_message = broker_on_message
    mqttc.on_connect = broker_on_connect
    mqttc.on_disconnect = broker_on_disconnect
    mqttc.on_publish = broker_on_publish
    mqttc.on_subscribe = broker_on_subscribe

    try:
        mqttc.username_pw_set(user, password)  #put your own mqtt user and password here if you are using them, otherwise comment out
        mqttc.connect(broker, 1883, 60) #Ping MQTT broker every 60 seconds if no data is published from this script.

    except Exception as e:
        print("Unable to connect to MQTT Broker: %s" % e)
        mqttc = None

#myroomba = Roomba()  #minnimum required to connect on Linux Debian system, will read connection from config file
myroomba = Roomba(address, blid, roombaPassword, topic="#", continuous=True, clean=False, cert_name = "/etc/ssl/certs/Go_Daddy_Root_Certificate_Authority_-_G2.pem")  #setting things manually

#all these are optional, if you don't include them, the defaults will work just fine
#if you are using maps
# 11m x 11m + 5m Y DIFF to cover upper foor
# 650 x 1020
# 1100 / 2 - 100 = 450
# 1370 / 2 - 335 = 350
#myroomba.enable_map(enable=True, enableMapWithText=False, roomOutline=False, rssiMap=True, rssiMapGoodSignal=-30, rssiMapBadSignal=-70, auto_rotate=False, mapSize="(1100,1370,-100,-240,0,0)", mapPath="/dataDisk/htdocs/roomba", iconPath="/dataDisk/Roomba980-Python/roomba/res/")  #enable live maps, class default is 
myroomba.enable_map(enable=True, enableMapWithText=False, roomOutline=False, auto_rotate=False, mapSize="(1100,1370,-100,-250,0,0)", mapPath="{{htdocs_path}}roomba", iconPath="/opt/roomba/res/")  #enable live maps, class default is no maps


if broker is not None:
    myroomba.set_mqtt_client(mqttc, brokerFeedback) #if you want to publish Roomba data to your own mqtt broker (default is not to) if you have more than one roomba, and assign a roombaName, it is addded to this topic (ie brokerFeedback/roombaName)
#finally connect to Roomba - (required!)
myroomba.connect()

print("<CMTRL C> to exit")
print("Subscribe to /roomba/feedback/# to see published data")

try:
    if mqttc is not None:
        mqttc.loop_forever()
    else:
        while True:
            #print("Roomba Data: %s" % json.dumps(myroomba.master_state, indent=2))
            time.sleep(5)

except (KeyboardInterrupt, SystemExit):
    print("System exit Received - Exiting program")
    myroomba.disconnect()
    if mqttc is not None:
        mqttc.disconnect()
