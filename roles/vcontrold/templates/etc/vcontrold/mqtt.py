import subprocess
import signal
import sys
from datetime import datetime
import time
import paho.mqtt.client as mqtt
import telnetlib
import re

class Handler(object):
    '''Handler client'''
    def __init__(self):
        self.terminated = False
        self.connected = False
        self.process = None
        self.telnet_client = None
        self.mqtt_client = None
        self.lastPublishTime = datetime.now()
        self.retryCount = 0

        self.cmds = ['getTempAussen', 'getTempAussenGedaempft', 'getTempVorlaufSoll','getTempVorlauf','getTempKesselSoll','getTempKessel','getHeizkreisPumpeDrehzahl','getBrennerStarts','getBrennerStunden','getTempWasserSpeicher','getTempSolarKollektor','getSolarStunden','getTempSolarSpeicher','getSolarLeistung','getSammelstoerung','getLeistungIst','getBetriebsart','getTempRaumSoll','getSolarPumpeStatus','getNachladeunterdrueckungStatus']

    def startDaemon(self):
        print("Start vcontrold ...", end='', flush=True)
        self.process = subprocess.Popen(['/usr/sbin/vcontrold', '-n'], stdout=subprocess.PIPE, universal_newlines=True)
        time.sleep(1)
        if self.damonIsAlive():
            print(" successful", flush=True)
        else:
            print(" failed", flush=True)
            raise Exception("Vcontrold not started") 
          
    def connectDaemon(self):
        try:
            print("Connect to vcontrold ...", end='', flush=True)
            if self.telnet_client is not None:
                self.telnet_client.close()
            self.telnet_client = telnetlib.Telnet("localhost", "3002")
            out = self.telnet_client.read_until(b"vctrld>",10)
            if len(out) == 0:
                print(" failed", flush=True)
                self.telnet_client.close()
                raise Exception("Vcontrold not readable") 
            print(" connected", flush=True)
        except:
            print(" failed", flush=True)
            raise Exception("Vcontrold not running") 
          
    def connectMqtt(self):
        try:
            print("Connect to mqtt ...", end='', flush=True)
            if self.mqtt_client is not None:
                self.mqtt_client.disconnect()
            self.mqtt_client = mqtt.Client()
            self.mqtt_client.on_connect = lambda client, userdata, flags, rc: self.on_connect(client, userdata, flags, rc)
            self.mqtt_client.on_disconnect = lambda client, userdata, rc: self.on_disconnect(client, userdata, rc)
            self.mqtt_client.on_message = lambda client, userdata, msg: self.on_message(client, userdata, msg) 
            self.mqtt_client.connect("mosquitto", 1883, 60)
            print(" connected", flush=True)
            startTime = datetime.now()
            while (datetime.now() - startTime).total_seconds() < 10:
                self.mqtt_client.loop()
                if self.terminated or self.connected:
                    break
            if not self.terminated and not self.connected:
                raise Exception("Mqtt connection not acknowledged") 
        except:
            print(" failed", flush=True)
            self.telnet_client.close()
            raise Exception("Mqtt not running") 
          
    def loop(self):
        #print("Loop", flush=True)
        self.mqtt_client.loop()
        
        while not self.terminated and not self.connected:
            print("Try reconnect to mqtt", flush=True)
            try:
                self.mqtt_client.reconnect()
                startTime = datetime.now()
                while (datetime.now() - startTime).total_seconds() < 10:
                    self.mqtt_client.loop()
                    if self.terminated or self.connected:
                        break
                if not self.terminated and not self.connected:
                    raise Exception("Mqtt connection not acknowledged") 
            except:
                time.sleep(5)
        
        if not self.terminated:
            dateTime = datetime.now()
            if dateTime.second == 0 or (dateTime - self.lastPublishTime).total_seconds() >= 60 :
                self.lastPublishTime = dateTime
                self.publish()
                
        self.retryCount = 0

    def on_connect(self,client,userdata,flags,rc):
        print("Connected to mqtt with result code:"+str(rc), flush=True)
        if rc == 0:
            self.connected = True
            # subscribe for all devices of user
            client.subscribe('+/vcontrol/setBetriebsartTo')
        
    def on_disconnect(self,client, userdata, rc):
        print("Disconnect from mqtt with result code:"+str(rc), flush=True)
        self.connected = False

    def on_message(self,client,userdata,msg):
        if not self.damonIsAlive():
            raise Exception("Vcontrold died") 
        
        print("Topic " + msg.topic + ", message:" + str(msg.payload), flush=True)
        
        cmd = "setBetriebsartTo{}".format(int(float(msg.payload.decode("ascii"))))
        self.telnet_client.write(cmd.encode('ascii') + b"\n")
        out = self.telnet_client.read_until(b"vctrld>",10)
        if len(out) == 0:
            print("Set '" + cmd + "' not successful", flush=True, file=sys.stderr)
        else:
            print("Set '" + cmd + "' successful", flush=True)
        
    def publish(self):
        if not self.damonIsAlive():
            raise Exception("Vcontrold died") 
          
        print("Publish values to mqtt ...", end='', flush=True)
        try:
            for cmd in self.cmds:
                self.telnet_client.write(cmd.encode('ascii') + b"\n")
                out = self.telnet_client.read_until(b"vctrld>",10)
                if len(out) == 0:
                    print(" failed with empty result", flush=True, file=sys.stderr)
                    return
                else:
                    search = re.search(r'[0-9]*\.?[0-9]+', out.decode("ascii"))
                    if search == None:
                        self.mqtt_client.publish('/vcontrol/getSammelstoerung', payload=999, qos=0, retain=False)
                        print(out.decode("ascii"), flush=True, file=sys.stderr)
                    else:
                        self.mqtt_client.publish('/vcontrol/' + cmd, payload=round(float(search.group(0)),2), qos=0, retain=False)                            
            print(" successful", flush=True)
        except Exception as e:
            print(" failed", flush=True)
            print(str(e), flush=True, file=sys.stderr)
          
    def terminate(self):
        if self.process != None:
            if self.damonIsAlive():
                print("Shutdown vcontrold", flush=True)
                self.process.terminate()
            self.process = None
      
        if self.telnet_client != None:
            print("Close connection to vcontrold", flush=True)
            self.telnet_client.close()
            self.telnet_client = None
            
        if self.mqtt_client != None:
            print("Close connection to mqtt", flush=True)
            self.mqtt_client.disconnect()
            self.mqtt_client = None
            
        self.terminated = True
        
    def isTerminated(self):
        return self.terminated
      
    def damonIsAlive(self):
        return self.process.poll() == None
      
    def canRetry(self,e):
        self.retryCount = self.retryCount + 1
        if self.retryCount > 10 or not self.damonIsAlive():
            print(str(e), flush=True, file=sys.stderr)
            return False
        elif not handler.isTerminated():
            print("Retry: {}".format(str(e)), flush=True)
            return True
      
handler = Handler()

def cleanup(signum, frame):
    #print(signum)
    #print(frame)
    print("Shutdown vclient", flush=True)
    handler.terminate()
    exit(0)

signal.signal(signal.SIGTERM, cleanup)
signal.signal(signal.SIGINT, cleanup)

try:
    handler.startDaemon()
except Exception as e:
    print(str(e), flush=True, file=sys.stderr)
    exit(1)
    
while True:
    try:
        handler.connectDaemon()
        handler.connectMqtt()
                
        print("Start event loop", flush=True)
        while not handler.isTerminated():          
            handler.loop()   
        print("End event loop", flush=True)
        break
    except Exception as e:
        if not handler.canRetry(e):
            break
        time.sleep(1)

if not handler.isTerminated():
    print("Shutdown handler", flush=True)
    handler.terminate()
    exit(1)
else:
    exit(0)
