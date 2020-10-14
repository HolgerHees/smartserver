import subprocess
import signal
import sys
from datetime import datetime
import time
import paho.mqtt.client as mqtt
import telnetlib
import re

class vclient(object):
    '''vcontrol client'''
    def __init__(self):
        self.cmds = ['timestamp', 'getTempAussen', 'getTempAussenGedaempft', 'getTempVorlaufSoll','getTempVorlauf','getTempKesselSoll','getTempKessel','getHeizkreisPumpeDrehzahl','getBrennerStarts','getBrennerStunden','getTempWasserSpeicher','getTempSolarKollektor','getSolarStunden','getTempSolarSpeicher','getSolarLeistung','getSammelstoerung','getLeistungIst','getBetriebsart','getTempRaumSoll','getSolarPumpeStatus','getNachladeunterdrueckungStatus']
        
        try:
            print("Connect to vcontrold ...", end='', flush=True)
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

        try:
            print("Connect to mqtt ...", end='', flush=True)
            self.mqtt_client = mqtt.Client()
            self.mqtt_client.on_connect = lambda client, userdata, flags, rc: self.on_connect(client, userdata, flags, rc)
            self.mqtt_client.on_message = lambda client, userdata, msg: self.on_message(client, userdata, msg) 
            self.mqtt_client.connect("mosquitto", 1883, 60)
            print(" connected", flush=True)
        except:
            print(" failed", flush=True)
            self.telnet_client.close()
            raise Exception("Mqtt not running") 

    def loop(self):
        #print("Loop", flush=True)
        self.mqtt_client.loop()

    def on_connect(self,client,userdata,flags,rc):
        print("Connected with result code:"+str(rc), flush=True)
        # subscribe for all devices of user
        client.subscribe('+/vcontrol/setBetriebsartTo')

    def on_message(self,client,userdata,msg):
        print("Topic " + msg.topic + ", message:" + str(msg.payload), flush=True)
        
        cmd = "setBetriebsartTo{}".format(int(float(msg.payload.decode("ascii"))))
        self.telnet_client.write(cmd.encode('ascii') + b"\n")
        out = self.telnet_client.read_until(b"vctrld>",10)
        if len(out) == 0:
            print("Set '" + cmd + "' not successful", flush=True)
        else:
            print("Set '" + cmd + "' successful", flush=True)
        
    def publish(self):
        print("Publish values to mqtt", flush=True)
        for cmd in self.cmds:
            '''Query & Publish'''
            if cmd == 'timestamp':
                timestamp = int(time.mktime(datetime.now().timetuple())) #unix time
                self.mqtt_client.publish('/vcontrol/' + cmd, payload=timestamp, qos=0, retain=False)	    
            else:
                self.telnet_client.write(cmd.encode('ascii') + b"\n")
                out = self.telnet_client.read_until(b"vctrld>",10)
                if len(out) == 0:
                    print("Publish not successful", flush=True)
                    return
                else:
                    search = re.search(r'[0-9]*\.?[0-9]+', out.decode("ascii"))
                    if search == None:
                        self.mqtt_client.publish('/vcontrol/getSammelstoerung', payload=999, qos=0, retain=False)
                        print(out.decode("ascii"), flush=True, file=sys.stderr)
                    else:
                        self.mqtt_client.publish('/vcontrol/' + cmd, payload=round(float(search.group(0)),2), qos=0, retain=False)
        print("Publish successful", flush=True)
                
    def terminate(self):
        if self.telnet_client != None:
            self.telnet_client.close()
        if self.mqtt_client != None:
            self.mqtt_client.disconnect()
    
print("Start vcontrold", flush=True)
process = subprocess.Popen(['/usr/sbin/vcontrold', '-n'], stdout=subprocess.PIPE, universal_newlines=True)
time.sleep(1)

i = 0
while i < 10:
    try:
        print("Init vclient client", flush=True)
        vc = vclient()
        
        def cleanup(signum, frame):
            #print(signum)
            #print(frame)
            print("Shutdown vcontrold", flush=True)
            process.terminate()

            print("Shutdown vclient", flush=True)
            vc.terminate()
            
            exit(0)

        signal.signal(signal.SIGTERM, cleanup)
        signal.signal(signal.SIGINT, cleanup)
        
        i = 0
        
        print("Start event loop", flush=True)
        run = True
        lastPublishTime = datetime.now()
        while run:
            return_code = process.poll()
            if return_code != None:
                break
          
            vc.loop()
            
            dateTime = datetime.now()
            
            if dateTime.second == 0 or (dateTime - lastPublishTime).total_seconds() >= 60 :
                lastPublishTime = dateTime
                vc.publish()
        
        #print("closed", flush=True)
        break
    except:
        print("Retry", flush=True)
        time.sleep(1)
        i = i + 1      

#print("finish", flush=True)

if process != None:
    return_code = process.poll()
    if return_code == None:
        process.terminate()

exit(1)
