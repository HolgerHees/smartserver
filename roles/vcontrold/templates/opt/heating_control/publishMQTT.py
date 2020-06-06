import time
import datetime
import telnetlib
import re
import paho.mqtt.client as mqtt


class vclient(object):
    '''vcontrol client'''
    def __init__(self):
        self.telnet_client = telnetlib.Telnet("localhost", "3002")
        self.telnet_client.read_until(b"vctrld>")
        
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.connect("mosquitto", 1883, 60)

    def publish(self, cmd):
        #print(cmd)
      
        '''Query & Publish'''
        if cmd == 'timestamp':
            timestamp = int(time.mktime(datetime.datetime.now().timetuple())) #unix time
            self.mqtt_client.publish('/vito/' + cmd, payload=timestamp, qos=0, retain=False)	    
        else:
            self.telnet_client.write(cmd.encode('ascii') + b"\n")

            out = self.telnet_client.read_until(b"vctrld>")

            search = re.search(r'[0-9]*\.?[0-9]+', out.decode("ascii"))
            
            # return search.group(0)
            self.mqtt_client.publish('/vito/' + cmd, payload=round(float(search.group(0)),2), 
qos=0, 
retain=False)

vals = ['timestamp', 'getTempAussen', 'getTempAussenGedaempft', 'getTempVorlaufSoll','getTempVorlauf','getTempKesselSoll','getTempKessel','getHeizkreisPumpeDrehzahl','getBrennerStarts','getBrennerStunden','getTempWasserSpeicher','getTempSolarKollektor','getSolarStunden','getTempSolarSpeicher','getSolarLeistung','getSammelstoerung','getLeistungIst','getBetriebsart','getTempRaumSoll','getSolarPumpeStatus','getNachladeunterdrueckungStatus']

vc = vclient()

for v in vals:
    vc.publish(v)
 
