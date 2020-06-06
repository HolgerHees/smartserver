import telnetlib
import paho.mqtt.client as mqtt

class vclient(object):
    '''vcontrol client'''
    def __init__(self):
        self.telnet_client = telnetlib.Telnet("localhost", "3002")
        self.telnet_client.read_until(b"vctrld>")
        
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect=self.on_connect
        self.mqtt_client.on_message=self.on_message
        self.mqtt_client.connect("mosquitto", 1883, 60)
        
    def loop(self):
        self.mqtt_client.loop()

    def on_connect(self,client,userdata,rc):
        print("Connected with result code:"+str(rc))
        # subscribe for all devices of user
        client.subscribe('+/vito/+/set')

    def on_message(self,client,userdata,msg):
        print("Topic " + msg.topic + "\nMessage:" + str(msg.payload))
    
vc = vclient()

run = True
while run:
    vc.loop()

 
