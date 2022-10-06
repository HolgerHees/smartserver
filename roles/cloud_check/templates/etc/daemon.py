import signal
import paho.mqtt.client as mqtt
import sys
import subprocess

import traceback

import time

import requests

import config

class Handler(object):
    '''Handler client'''
    def __init__(self):
        self.mqtt_client = None
        
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
            error_count = 0

            published = {}
            try:
                for peer in config.cloud_peers:
                    host = config.cloud_peers[peer]
                    is_reachable = 0
                    try:
                        #print("http://{}/state".format(host))
                        response = requests.get("http://{}/state".format(host), allow_redirects = False, timeout = 5 )
                        #self.log.info("{} {} {}".format(peer,response_code == 200,response_body == "online"))
                        is_reachable = 2 if response.status_code == 200 and response.text.rstrip() == "online" else 1
                        #self.log.info("{}".format(is_reachable))
                    except Exception as e:
                        #print(e)
                        #state_result = Exec.executeCommandLine(Duration.ofSeconds(100),"/usr/bin/wget","-O", "-", "http://{}/state".format(host))
                        #self.log.error(state_result)
                        #self.log.error(u"network cloud ({}) http data exception: {}".format(peer,e))
                        pass

                    if is_reachable == 0:
                        try:
                            result = subprocess.run(["/bin/ping","-W", "5", "-c", "1", host], shell=False, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT )
                            if result.returncode == 0:
                                is_reachable = 1
                        except Exception as e:
                            print(u"network cloud ({}) ping data exception: {}".format(peer,e))
                            pass

                    #print("{} {}".format(peer,is_reachable))

                    published[peer] = is_reachable
                    self.mqtt_client.publish("{}/cloud/peer/{}/".format(config.peer_name,peer), payload=is_reachable, qos=0, retain=False)

                sleep_time = 60

                error_count = 0                
            except Exception as e:
                error_count += 1
                sleep_time = 60 * error_count if error_count < 6 else 360
                try:
                    raise e
                except (CurrentDataException,ForecastDataException) as e:
                    print("{}: {}".format(str(e.__class__),str(e)), flush=True, file=(sys.stderr if error_count > 3 else sys.stdout))
                except (RequestDataException,AuthException,requests.exceptions.RequestException) as e:
                    print("{}: {}".format(str(e.__class__),str(e)), flush=True, file=sys.stderr)

            print("Published: {}, Sleep now for {} seconds".format(published, sleep_time),flush=True)
            time.sleep(sleep_time)

            #requests.exceptions.ConnectionError, urllib3.exceptions.MaxRetryError, urllib3.exceptions.NewConnectionError

    def on_connect(self,client,userdata,flags,rc):
        print("Connected to mqtt with result code:"+str(rc), flush=True)
        
    def on_disconnect(self,client, userdata, rc):
        print("Disconnect from mqtt with result code:"+str(rc), flush=True)

    def on_message(self,client,userdata,msg):
        pass
            
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
