import subprocess
import signal
import sys
from datetime import datetime, timedelta
import time
import paho.mqtt.client as mqtt
import sys
import pexpect
import re

class Handler(object):
    '''Handler client'''
    def __init__(self):
        self.terminated = False
        self.process = None
        self.telnet_client = None
        self.mqtt_client = None
        self.lastPublishTime = datetime.now() - timedelta(minutes=10)

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
        retryCount = 0
        while retryCount <= 5:
            try:
                print("Connection to vcontrold ...", end='', flush=True)
                self.telnetOpen()
                print(" initialized", flush=True)

                self.telnetReadUntil(b"vctrld>", 10)
                print("Connection to vcontrold successful", flush=True)
                break
            except pexpect.TIMEOUT:
                raise Exception("Vcontrold not readable")
            except:
                self.telnetClose()

                print("Connection to vcontrold failed", flush=True)

                retryCount = retryCount + 1
                time.sleep(1)
                #raise Exception("Vcontrold not running")

    def telnetClose(self):
        if self.telnet_client != None:
            self.telnet_client.close()
            self.telnet_client = None

    def telnetOpen(self):
        self.telnet_client = pexpect.spawn("telnet localhost 3002")
        #self.telnet_client.logfile = sys.stdout.buffer

    def telnetReadUntil(self, promt, timeout):
        self.telnet_client.expect(promt, timeout=timeout)
        return self.telnet_client.before

    def telnetWrite(self, data):
        return self.telnet_client.write(data)

    def connectMqtt(self):
        print("Connection to mqtt ...", end='', flush=True)
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = lambda client, userdata, flags, rc: self.on_connect(client, userdata, flags, rc)
        self.mqtt_client.on_disconnect = lambda client, userdata, rc: self.on_disconnect(client, userdata, rc)
        self.mqtt_client.on_message = lambda client, userdata, msg: self.on_message(client, userdata, msg)
        self.mqtt_client.connect("mosquitto", 1883, 60)
        print(" initialized", flush=True)

        self.mqtt_client.loop_start()

    def loop(self):
        dateTime = datetime.now()
        if dateTime.second == 0 or (dateTime - self.lastPublishTime).total_seconds() >= 60 :
            self.lastPublishTime = dateTime
            self.publish()
        else:
            time.sleep(60-(dateTime - self.lastPublishTime).total_seconds())

    def on_connect(self,client,userdata,flags,rc):
        print("Connected to mqtt with result code:"+str(rc), flush=True)
        if rc == 0:
            # subscribe for all devices of user
            client.subscribe('vcontrol/setBetriebsartTo')

    def on_disconnect(self,client, userdata, rc):
        print("Disconnect from mqtt with result code:"+str(rc), flush=True)

    def on_message(self,client,userdata,msg):
        if not self.damonIsAlive():
            raise Exception("Vcontrold died")

        print("Topic " + msg.topic + ", message:" + str(msg.payload), flush=True)

        cmd = "setBetriebsartTo{}".format(int(float(msg.payload.decode("ascii"))))

        self.telnetWrite(cmd.encode('ascii') + b"\n")
        try:
            self.telnetReadUntil(b"vctrld>",10)
            print("Set '" + cmd + "' successful", flush=True)
        except pexpect.TIMEOUT:
            print("Set '" + cmd + "' not successful", flush=True, file=sys.stderr)

    def publish(self):
        if not self.damonIsAlive():
            raise Exception("Vcontrold died")

        print("Publish values to mqtt ...", end='', flush=True)
        try:
            for cmd in self.cmds:
                self.telnetWrite(cmd.encode('ascii') + b"\n")
                try:
                    out = self.telnetReadUntil(b"vctrld>",10)
                    search = re.search(r'[-]?[0-9]*\.?[0-9]+', out.decode("ascii"))
                    if search == None:
                        self.mqtt_client.publish('vcontrol/getSammelstoerung', payload=999, qos=0, retain=False)
                        print(out.decode("ascii"), flush=True, file=sys.stderr)
                    else:
                        self.mqtt_client.publish('vcontrol/' + cmd, payload=round(float(search.group(0)),2), qos=0, retain=False)
                except pexpect.TIMEOUT:
                    print(" failed with empty result", flush=True, file=sys.stderr)
                    return
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
            self.telnetClose()

            print("Close connection to mqtt", flush=True)
            self.mqtt_client.loop_stop()
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

    handler.connectMqtt()

    handler.connectDaemon()
except Exception as e:
    print(str(e), flush=True, file=sys.stderr)
    exit(1)

print("Start event loop", flush=True)
while not handler.isTerminated():
    handler.loop()
print("End event loop", flush=True)

if not handler.isTerminated():
    print("Shutdown handler", flush=True)
    handler.terminate()
    exit(1)
else:
    exit(0)
