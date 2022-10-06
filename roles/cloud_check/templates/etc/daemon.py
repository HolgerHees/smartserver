import signal
import paho.mqtt.client as mqtt
import sys
import subprocess

import traceback

import time
from datetime import datetime

import requests

import config

class Handler(object):
    '''Handler client'''
    def __init__(self):
        self.is_online = False
        self.mqtt_client = None

        self.mount_last_notified = {}
        self.mount_errors = {}

        self.state_errors = {}
        self.ping_errors = {}

    def connectMqtt(self):
        print("Connection to mqtt ...", end='', flush=True)
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = lambda client, userdata, flags, rc: self.on_connect(client, userdata, flags, rc)
        self.mqtt_client.on_disconnect = lambda client, userdata, rc: self.on_disconnect(client, userdata, rc)
        self.mqtt_client.on_message = lambda client, userdata, msg: self.on_message(client, userdata, msg) 
        self.mqtt_client.connect(config.mosquitto_host, 1883, 60)
        print(" initialized", flush=True)
        
        self.mqtt_client.loop_start()

    def _processState(self,peer,errors,is_success):
        if is_success:
            if peer in errors:
                del errors[peer]
        else:
            errors[peer] = True

    def _getTimeout(self,peer,errors):
        if peer in errors:
            return 1
        return 5

    def _check_online_state(self):
        self.is_online = self._ping(None, "8.8.8.8")
        if not self.is_online:
            self.mount_last_notified = {}
            self.mount_errors = {}

            self.state_errors = {}
            self.ping_errors = {}

            sleep_time = 300
            print("No internet connection. Suspent for {} seconds".format(sleep_time), flush=True, file=sys.stderr)
            time.sleep(sleep_time)
        return self.is_online

    def _checkmount(self, peer):
        try:
            result = subprocess.run(["/bin/mountpoint","-q","/cloud/remote/{}".format(peer)], shell=False, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout = self._getTimeout(peer,self.mount_errors) )
            is_success = result.returncode == 0
        except Exception as e:
            is_success = False

        self._processState(peer, self.mount_errors, is_success)
        return is_success

    def _checkstate(self, peer, host):
        is_reachable = 0
        try:
            #print("http://{}/state".format(host))
            response = requests.get("http://{}/state".format(host), allow_redirects = False, timeout = self._getTimeout(peer,self.state_errors) )
            #self.log.info("{} {} {}".format(host,response_code == 200,response_body == "online"))
            is_reachable = 2 if response.status_code == 200 and response.text.rstrip() == "online" else 1
        except Exception as e:
            pass

        self._processState(peer, self.state_errors, is_reachable != 0)
        return is_reachable

    def _ping(self, peer, host):
        try:
            result = subprocess.run(["/bin/ping","-W", str(self._getTimeout(peer,self.ping_errors)), "-c", "1", host], shell=False, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT )
            is_success = result.returncode == 0
        except Exception as e:
            is_success = False

        self._processState(peer, self.ping_errors, is_success)
        return is_success

    def loop(self):
        #status = os.fdopen(self.dhcpListenerProcess.stdout.fileno())
        #status = os.fdopen(os.dup(self.dhcpListenerProcess.stdout.fileno()))
        
        while True:
            if not self.is_online and not self._check_online_state():
                continue

            error_count = 0
            published = {}
            try:
                for peer in config.cloud_peers:
                    host = config.cloud_peers[peer]
                    is_reachable = self._checkstate(peer, host)

                    # CHECK STATE URL
                    if is_reachable == 0 and self._ping(peer, host):
                        is_reachable = 1

                    # CHECK PING
                    if is_reachable == 0 and not self._check_online_state():
                        break

                    # PUBLISH
                    #print("{} {}".format(peer,is_reachable))
                    self.mqtt_client.publish("{}/cloud/peer/{}/".format(config.peer_name,peer), payload=is_reachable, qos=0, retain=False)
                    published[peer] = is_reachable

                    # CHECK mountpoint
                    if not self._checkmount(peer):
                        if not self._check_online_state():
                            break

                        if peer not in self.mount_last_notified or (datetime.now() - self.mount_last_notified[peer]).total_seconds() > 3600:
                            print("Cloud nfs mount from peer '{}' has problem".format(peer), flush=True, file=sys.stderr)
                            self.mount_last_notified[peer] = datetime.now()

                    elif peer in self.mount_last_notified:
                        print("Cloud nfs mount from peer '{}' is available again".format(peer), flush=True)
                        del self.mount_last_notified[peer]

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

            if self.is_online:
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
