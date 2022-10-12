import signal
import threading
import paho.mqtt.client as mqtt
import sys
import subprocess

import traceback

import time
from datetime import datetime, timedelta

from flask import Flask, request, make_response
from werkzeug.serving import WSGIRequestHandler

import logging

import requests

import config

CHECK_INTERVAL = 60

MESH_OFFLINE_TIMEOUT = 300

PEER_STATE_OFFLINE = 0
PEER_STATE_PING_OK = 1
PEER_STATE_ONLINE  = 2
PEER_STATE_UNKNOWN = -1

MOUNT_STATE_UNMOUNTED = 0
MOUNT_STATE_MOUNTED = 1
MOUNT_STATE_UNKNOWN = -1

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
    def getAgeInSeconds(ref_datetime):
        return (datetime.now() - ref_datetime).total_seconds()

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

        self.last_running_state = PEER_STATE_UNKNOWN
        self.last_mount_state = MOUNT_STATE_UNMOUNTED

        self.error_count = 0

    def _getTimeout(self,has_error):
        if has_error:
            return 1
        return 5

    def _checkmount(self, peer):
        try:
            result = subprocess.run(["/bin/mountpoint","-q","/cloud/remote/{}".format(peer)], shell=False, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout = self._getTimeout(self.has_mount_error) )
            is_success = result.returncode == 0
        except subprocess.TimeoutExpired as e:
            is_success = False
            Helper.logInfo("Mount timeout for peer {}".format(peer))
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
            running_state = PEER_STATE_ONLINE if response.status_code == 200 and response.text.rstrip() == "online" else PEER_STATE_OFFLINE
        except (requests.exceptions.ConnectionError,requests.exceptions.ReadTimeout) as e:
            running_state = PEER_STATE_OFFLINE
            Helper.logInfo("State connection error for peer {}".format(peer))
        except Exception as e:
            running_state = PEER_STATE_OFFLINE
            Helper.logError("State check exception {} - {}".format(type(e), str(e)))

        self.has_state_error = running_state == PEER_STATE_OFFLINE
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

        while self.is_running:
            sleep_time = CHECK_INTERVAL

            if not self.is_suspended:
                try:
                    start = time.time()

                    # **** CHECK STATE URL ****
                    running_state = self._checkstate(self.peer, self.data["host"])

                    # **** CHECK PING ****
                    if running_state == PEER_STATE_OFFLINE and self._ping(self.peer, self.data["host"]):
                        running_state = PEER_STATE_PING_OK

                    if running_state == PEER_STATE_OFFLINE:
                        self.is_suspended = None

                        # **** CONFIRM THAT WE ARE ONLINE ****
                        self.handler.forceOnlineCheck()
                        self.event.wait()
                        self.event.clear()

                    if self.handler.isOnline():
                        # **** PUBLISH ****
                        #print("{} {}".format(self.peer,running_state))
                        if self.last_running_state != running_state:
                            Helper.logInfo("New state for pear '{}' is '{}'".format(self.peer, running_state))
                        self.mqtt_client.publish("{}/cloud/peer/{}".format(config.peer_name,self.peer), payload=running_state, qos=0, retain=False)
                        self.last_running_state = running_state

                        if running_state == PEER_STATE_ONLINE:
                            # CHECK mountpoint
                            if not self._checkmount(self.peer):
                                self.last_mount_state = MOUNT_STATE_UNMOUNTED
                            else:
                                self.last_mount_state = MOUNT_STATE_MOUNTED
                        else:
                            self.last_mount_state = MOUNT_STATE_UNKNOWN

                    end = time.time()
                    sleep_time = sleep_time - (end-start)
                    self.error_count = 0
                except Exception as e:
                    self.error_count += 1
                    sleep_time = ( sleep_time * self.error_count ) if self.error_count < 6 else 360
                    Helper.logError("Main loop exception {} - {}".format(type(e), str(e)))

            if sleep_time > 0:
                self.event.wait(sleep_time)
            self.event.clear()

            if not self.is_running:
                break

    def getPeer(self):
        return self.peer

    def isOnline(self):
        return self.last_running_state == PEER_STATE_ONLINE

    def getMountState(self):
        return self.last_mount_state

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
            Helper.logInfo("{} polling job for peer '{}'".format("Resume" if self.last_running_state >= PEER_STATE_OFFLINE else "Start", self.peer))

    def terminate(self):
        self.is_running = False
        self.event.set()

        Helper.logInfo("Terminate polling job for peer '{}'".format(self.peer))

class Handler(threading.Thread):
    '''Handler client'''
    def __init__(self):
        threading.Thread.__init__(self)

        self.is_running = True

        self.is_online = False
        self.is_checking = True

        self.mqtt_client = None

        self.peer_jobs = {}
        self.watched_topics = {}

        self.state_metrics = []

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

    def initWatchedTopics(self, is_online):
        watched_topics = {}
        if is_online:
            for peer in config.cloud_peers:
                topic = "{}/cloud/peer/{}".format(config.peer_name,peer)
                watched_topics[topic] = { "updated": datetime.now(), "state": PEER_STATE_UNKNOWN }

                topic = "{}/cloud/peer/{}".format(peer,config.peer_name)
                watched_topics[topic] = { "updated": datetime.now(), "state": PEER_STATE_UNKNOWN }

                for _peer in config.cloud_peers:
                    if peer == _peer:
                        continue

                    topic = "{}/cloud/peer/{}".format(peer,_peer)
                    watched_topics[topic] = { "updated": datetime.now(), "state": PEER_STATE_UNKNOWN }
        self.watched_topics = watched_topics

    def isOnline(self):
        return self.is_online

    def getStateMetrics(self):
        if self.is_online:
            state_metrics = []

            # **** CHECK MISSING TOPICS ****
            topic_state = {}
            for watched_topic in self.watched_topics:
                topic_data = self.watched_topics[watched_topic]
                source_peer = watched_topic.split("/")[0]
                target_peer = watched_topic.split("/")[-1]

                if source_peer not in topic_state:
                    if source_peer in self.peer_jobs and not self.peer_jobs[source_peer].isOnline():
                        topic_state[source_peer] = -1
                    else:
                        topic_state[source_peer] = 0

                if Helper.getAgeInSeconds(topic_data["updated"]) < CHECK_INTERVAL * 2:
                    state_metrics.append("cloud_check_topic{{source_peer=\"{}\",target_peer=\"{}\"}} {}".format(source_peer,target_peer,int(topic_data["state"])))
                    topic_state[source_peer] = 1
                    continue
                else:
                    state_metrics.append("cloud_check_topic{{source_peer=\"{}\",target_peer=\"{}\"}} {}".format(source_peer,target_peer,PEER_STATE_UNKNOWN))
                    topic_data["state"] = PEER_STATE_UNKNOWN

            for peer in topic_state:
                state_metrics.append("cloud_check_peer_mqtt_state{{peer=\"{}\"}} {}".format(peer,topic_state[peer]))

            # **** CHECK IF ALL PEERS ARE ONLINE ****
            for peer in config.cloud_peers:
                max_state = PEER_STATE_UNKNOWN
                state_count = 0
                for watched_topic in self.watched_topics:
                    topic_data = self.watched_topics[watched_topic]
                    target_peer = watched_topic.split("/")[-1]

                    if target_peer != peer:
                        continue

                    state_count += 1

                    if max_state < int(topic_data["state"]):
                        max_state = int(topic_data["state"])

                #Helper.logInfo("{} {} {}".format(peer, max_state, state_count))

                # **** NOTIFY PEERS IF THEY ARE OFFLINE ****
                peer_job = self.peer_jobs[peer]
                if state_count == len(config.cloud_peers):
                    state_metrics.append("cloud_check_peer_online_state{{peer=\"{}\"}} {}".format(peer,max_state))
                else:
                    state_metrics.append("cloud_check_peer_online_state{{peer=\"{}\"}} {}".format(peer,PEER_STATE_UNKNOWN))

                state_metrics.append("cloud_check_peer_mount_state{{peer=\"{}\"}} {}".format(peer,peer_job.getMountState()))
        else:
            state_metrics = []

        return "{}\n".format( "\n".join(state_metrics) )

    def forceOnlineCheck(self):
        if self.is_checking:
            return

        self.is_checking = True
        self.event.set()

    def run(self):
        #status = os.fdopen(self.dhcpListenerProcess.stdout.fileno())
        #status = os.fdopen(os.dup(self.dhcpListenerProcess.stdout.fileno()))
        
        for peer in config.cloud_peers:
            host = config.cloud_peers[peer]["host"]
            job = PeerJob(peer, {"host": host}, self.mqtt_client, self)
            job.start()
            self.peer_jobs[peer] = job

        next_topic_checks = datetime.now()
        while self.is_running:
            if self.is_checking:
                # **** CHECK INTERNET CONNECTIVITY ****
                Helper.logInfo("Check internet connectivity")
                is_online = Helper.ping("8.8.8.8", 5)

                if self.is_online != is_online:
                    self.initWatchedTopics(is_online)

                self.is_online = is_online
                self.is_checking = False

                if not self.is_online:
                    for job in self.peer_jobs.values():
                        job.suspend()
                else:
                    for job in self.peer_jobs.values():
                        job.resume()

            #Helper.logInfo(sleep_time)
            self.event.wait( CHECK_INTERVAL )
            self.event.clear()

    def on_connect(self,client,userdata,flags,rc):
        Helper.logInfo("Connected to mqtt with result code:"+str(rc))

        for peer in config.cloud_peers:
            client.subscribe('+/cloud/peer/#')

    def on_disconnect(self,client, userdata, rc):
        Helper.logInfo("Disconnect from mqtt with result code:"+str(rc))

    def on_message(self,client,userdata,msg):
        #print("Topic " + msg.topic + ", message:" + str(msg.payload), flush=True)
        self.watched_topics[msg.topic] = { "updated": datetime.now(), "state": msg.payload }

    def terminate(self):
        self.is_running = False
        self.event.set()

        for job in self.peer_jobs.values():
            job.terminate()

        if self.mqtt_client != None:
            Helper.logInfo("Close connection to mqtt")
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()

app = Flask(__name__)

@app.route('/metrics/', methods = ['GET'])
def metrics():
    return handler.getStateMetrics()
        
logging_handler = logging.StreamHandler(sys.stdout)
logging.basicConfig(
    handlers = [logging_handler],
    level=logging.ERROR
    #format=logging.Formatter(fmt="[%(levelname)s] - %(module)s - %(message)s")
)

class ShutdownException(Exception):
    pass

def cleanup(signum, frame):
    raise ShutdownException()

signal.signal(signal.SIGTERM, cleanup)
signal.signal(signal.SIGINT, cleanup)

handler = Handler()
handler.connectMqtt()
handler.start()

try:
    WSGIRequestHandler.protocol_version = "HTTP/1.1"
    app.run(debug=False, use_reloader=False, threaded=True, host="0.0.0.0", port='80')
except ShutdownException as e:
    pass

handler.terminate()
exit(0)


