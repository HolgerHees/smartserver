import signal
import threading
import paho.mqtt.client as mqtt
import sys
import subprocess

import traceback

import time
from datetime import datetime

import requests

import config

check_interval = 60
grouped_message_timeout = 3600

class Helper(object):
    lastNotified = {}

    @staticmethod
    def ping(host, timeout):
        try:
            result = subprocess.run(["/bin/ping","-W", str(timeout), "-c", "1", host], shell=False, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT )
            is_success = result.returncode == 0
            #if not is_success:
            #    print("Polling host '{}' was not successful. CODE: {}, BODY: {}".format(host, result.returncode, result.stdout))
        except Exception as e:
            is_success = False

        return is_success

    @staticmethod
    def logInfo(msg, end="\n"):
        print(msg, end=end, flush=True)

    @staticmethod
    def logError(msg, end="\n"):
        print(msg, end=end, flush=True, file=sys.stderr)

    @staticmethod
    def logGroupedMsg(group, msg, timeout = None):
        if timeout is None:
            if group in Helper.lastNotified:
                Helper.logInfo(msg)
                del Helper.lastNotified[group]
        else:
            if group not in Helper.lastNotified or (datetime.now() - Helper.lastNotified[group]).total_seconds() > timeout:
                Helper.logError(msg)
                Helper.lastNotified[group] = datetime.now()

class PeerJob(threading.Thread):
    '''Device client'''
    def __init__(self, peer, data, mqtt_client, handler):
        threading.Thread.__init__(self)

        self.is_running = True
        self.is_suspended = True

        self.peer = peer
        self.data = data

        self.mqtt_client = mqtt_client
        self.handler = handler

        self.event = threading.Event()

        self.last_notified = None
        self.has_mount_error = False
        self.has_state_error = False
        self.has_ping_error = False

        self.last_running_state = -1

    def _getTimeout(self,has_error):
        if has_error:
            return 1
        return 5

    def _checkmount(self, peer):
        try:
            result = subprocess.run(["/bin/mountpoint","-q","/cloud/remote/{}".format(peer)], shell=False, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout = self._getTimeout(self.has_mount_error) )
            is_success = result.returncode == 0
        except Exception as e:
            is_success = False
            Helper.logError("Mount check exception {} - {}".format(type(e), str(e)))

        self.has_mount_error = not is_success
        return is_success

    def _checkstate(self, peer, host):
        try:
            #print("http://{}/state".format(host))
            response = requests.get("http://{}/state".format(host), allow_redirects = False, timeout = self._getTimeout(self.has_state_error) )
            #print("{} {}".format(response.status_code,response.text))
            #self.log.info("{} {} {}".format(host,response_code == 200,response_body == "online"))
            running_state = 2 if response.status_code == 200 and response.text.rstrip() == "online" else 1
        except requests.exceptions.ConnectionError as e:
            running_state = 0
            Helper.logInfo("State check connection error {} - {}".format(type(e), str(e)))
        except Exception as e:
            running_state = 0
            Helper.logError("State check exception {} - {}".format(type(e), str(e)))

        self.has_state_error = running_state == 0
        return running_state

    def _ping(self, peer, host):
        try:
            is_success = Helper.ping(host, self._getTimeout(self.has_ping_error))
        except Exception as e:
            is_success = False
            Helper.logError("Ping check exception {} - {}".format(type(e), str(e)))

        self.has_ping_error = not is_success
        return is_success

    def run(self):
        #print("Polling job for peer '{}' is initialized".format(self.peer))

        error_count = 0
        while self.is_running:
            sleep_time = check_interval

            if not self.is_suspended:
                try:
                    start = time.time()

                    host = self.data["host"]

                    # CHECK STATE URL
                    running_state = self._checkstate(self.peer, host)

                    # CHECK PING
                    if running_state == 0 and self._ping(self.peer, host):
                        running_state = 1

                    if running_state == 0:
                        self.is_suspended = None

                        self.handler.forceOnlineCheck()
                        self.event.wait()
                        self.event.clear()

                    if self.handler.isOnline():
                        # PUBLISH
                        #print("{} {}".format(self.peer,running_state))
                        if self.last_running_state != running_state:
                            Helper.logInfo("New state for pear '{}' is '{}'".format(self.peer, running_state))
                        self.mqtt_client.publish("{}/cloud/peer/{}".format(config.peer_name,self.peer), payload=running_state, qos=0, retain=False)
                        self.last_running_state = running_state

                        if running_state == 2:
                            # CHECK mountpoint
                            if not self._checkmount(self.peer):
                                Helper.logGroupedMsg("mount", "Cloud nfs mount of peer '{}' has problem".format(self.peer), grouped_message_timeout)
                            else:
                                Helper.logGroupedMsg("mount", "Cloud nfs mount of peer '{}' is available again".format(self.peer))

                    end = time.time()
                    sleep_time = sleep_time - (end-start)
                    error_count = 0
                except Exception as e:
                    error_count += 1
                    sleep_time = ( sleep_time * error_count ) if error_count < 6 else 360
                    Helper.logError("Main loop exception {} - {}".format(type(e), str(e)))

            if sleep_time > 0:
                self.event.wait(sleep_time)
            self.event.clear()

            if not self.is_running:
                break

    def suspend(self):
        if self.is_suspended:
            return

        show_log = self.is_suspended is not None

        self.is_suspended = True
        self.event.set()

        if show_log:
            Helper.logInfo("Suspend polling job for peer '{}'".format(self.peer))

    def resume(self):
        if self.is_suspended is not None and not self.is_suspended:
            return

        show_log = self.is_suspended is not None

        self.is_suspended = False
        self.event.set()

        if show_log:
            Helper.logInfo("{} polling job for peer '{}'".format("Resume" if self.last_running_state >= 0 else "Start", self.peer))

    def terminate(self):
        self.is_running = False
        self.event.set()

        Helper.logInfo("Terminate polling job for peer '{}'".format(self.peer))

class Handler(object):
    '''Handler client'''
    def __init__(self):
        self.is_online = False
        self.is_checking = True

        self.mqtt_client = None

        self.peer_checkers = []

        self.event = threading.Event()

    def connectMqtt(self):
        Helper.logInfo("Connection to mqtt ...", end='')
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = lambda client, userdata, flags, rc: self.on_connect(client, userdata, flags, rc)
        self.mqtt_client.on_disconnect = lambda client, userdata, rc: self.on_disconnect(client, userdata, rc)
        self.mqtt_client.on_message = lambda client, userdata, msg: self.on_message(client, userdata, msg) 
        self.mqtt_client.connect(config.mosquitto_host, 1883, 60)
        Helper.logInfo(" initialized")
        
        self.mqtt_client.loop_start()

    def isOnline(self):
        return self.is_online

    def forceOnlineCheck(self):
        if self.is_checking:
            return

        self.is_checking = True
        self.event.set()

    def loop(self):
        #status = os.fdopen(self.dhcpListenerProcess.stdout.fileno())
        #status = os.fdopen(os.dup(self.dhcpListenerProcess.stdout.fileno()))
        
        for peer in config.cloud_peers:
            host = config.cloud_peers[peer]
            checker = PeerJob(peer, {"host": host}, self.mqtt_client, self)
            checker.start()
            self.peer_checkers.append(checker)

        while True:
            if self.is_checking:
                Helper.logInfo("Check internet connectivity")
                self.is_online = Helper.ping("8.8.8.8", 5)
                self.is_checking = False

                if not self.is_online:
                    Helper.logGroupedMsg("internet", "Internet is down", grouped_message_timeout)

                    for checker in self.peer_checkers:
                        checker.suspend()
                else:
                    Helper.logGroupedMsg("internet", "Internet is up again")

                    for checker in self.peer_checkers:
                        checker.resume()

            self.event.wait(check_interval)
            self.event.clear()

    def on_connect(self,client,userdata,flags,rc):
        Helper.logInfo("Connected to mqtt with result code:"+str(rc))
        
    def on_disconnect(self,client, userdata, rc):
        Helper.logInfo("Disconnect from mqtt with result code:"+str(rc))

    def on_message(self,client,userdata,msg):
        pass
            
    def terminate(self):
        for checker in self.peer_checkers:
            checker.terminate()

        if self.mqtt_client != None:
            Helper.logInfo("Close connection to mqtt")
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
