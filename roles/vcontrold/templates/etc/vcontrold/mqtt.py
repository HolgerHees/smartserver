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
        
        self.telnet_client = telnetlib.Telnet("localhost", "3002")
        self.telnet_client.read_until(b"vctrld>")
        
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = lambda client, userdata, flags, rc: self.on_connect(client, userdata, flags, rc)
        self.mqtt_client.on_message = lambda client, userdata, msg: self.on_message(client, userdata, msg) 
        self.mqtt_client.connect("mosquitto", 1883, 60)
        
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
        out = self.telnet_client.read_until(b"vctrld>")
        
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
                out = self.telnet_client.read_until(b"vctrld>")

                search = re.search(r'[0-9]*\.?[0-9]+', out.decode("ascii"))
                if search == None:
                    self.mqtt_client.publish('/vcontrol/getSammelstoerung', payload=999, qos=0, retain=False)
                    print(out.decode("ascii"), flush=True, file=sys.stderr)
                else:
                    self.mqtt_client.publish('/vcontrol/' + cmd, payload=round(float(search.group(0)),2), qos=0, retain=False)
        print("Publish successful", flush=True)
                
    def terminate(self):
        self.mqtt_client.disconnect()
    
print("Start vcontrold", flush=True)
process = subprocess.Popen(['/usr/sbin/vcontrold', '-n'], stdout=subprocess.PIPE, universal_newlines=True)

print("Wait for vcontrold to become ready", flush=True)
i = 0
while i < 10:
    try:
        print("Init mqtt client", flush=True)
        vc = vclient()
        
        def cleanup(signum, frame):
            #print(signum)
            #print(frame)
            print("Shutdown vcontrold", flush=True)
            process.terminate()

            print("Shutdown mqtt", flush=True)
            vc.terminate()
            
            exit(0)

        signal.signal(signal.SIGTERM, cleanup)
        signal.signal(signal.SIGINT, cleanup)
        
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
        time.sleep(1)
        i = i + 1      

#print("finish", flush=True)

if process != None:
    return_code = process.poll()
    if return_code == None:
        process.terminate()

exit(1)
