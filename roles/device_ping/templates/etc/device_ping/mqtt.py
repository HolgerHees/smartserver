import subprocess
import signal
import sys
from datetime import datetime
import time
import paho.mqtt.client as mqtt
import re
from threading import Thread
import math
import queue
import os
import socket

devices = {
{% for username in userdata %}
{% if userdata[username].phone_device is defined %}
    {% if loop.index > 1 %},{% endif %}"phone_{{username}}": { "ip": "{{userdata[username].phone_device['ip']}}", "type": "{{userdata[username].phone_device['type'] | default('android')}}",  "timeout": {{userdata[username].phone_device['timeout'] | default(90)}} }
{% endif %}
{% endfor %}
}

interface = "{{main_network_interface}}"

class Helper():
    def knock(address_family,ip_address):
        s = socket.socket(address_family, socket.SOCK_DGRAM)
        s.setblocking(False)
        socket_address = (ip_address, 5353)
        s.sendto(b'', socket_address)
        s.close()
        
    def getAddressFamily(ip_address):
        address_family, _, _, _, (ip_address, _) = socket.getaddrinfo(
            host=ip_address,
            port=None,
            flags=socket.AI_ADDRCONFIG
        )[0]
        return address_family
          
class Device(Thread):
    '''Device client'''
    def __init__(self,name,device,interface,mqtt_client):
        Thread.__init__(self) 
        self.daemon = True # needed for threading to be killed automatically on restart
        
        self.name = name

        self.type = device['type']
        self.timeout = device['timeout']

        self.ip_address = device['ip']
        self.address_family = Helper.getAddressFamily(self.ip_address)
        self.interface = interface

        if self.type == "android":
            self.offlineArpRetries =  1
        else:
            # needed for multiple calls of 'knock' during offline check time
            self.offlineArpRetries =  int( math.floor( (self.timeout / 4) * 1 / 10 ) )
          
        # needed for multiple calls of 'ping' and 'knock' during online check time
        self.onlineArpRetries =  int( math.floor( (self.timeout / 4) * 3 / 10 ) )

        self.onlineArpCheckTime = int( math.floor( (self.timeout / 4) * 3 / self.onlineArpRetries ) )
        self.offlineArpCheckTime = int( math.floor( (self.timeout / 4) * 1 / self.offlineArpRetries ) )
        self.onlineSleepTime = self.timeout - (self.onlineArpRetries * self.onlineArpCheckTime)
        self.offlineSleepTime = self.timeout - (self.offlineArpRetries * self.offlineArpCheckTime)
                
        self.forcePublishTime = 60

        self.mqtt_client = mqtt_client
        
        self.isRunning = True
        self.process = None

        self.lastSeen = datetime(1, 1, 1, 0, 0)
        self.lastPublished = datetime(1, 1, 1, 0, 0)
        
        self.isOnline = None
      
    def run(self):
        print("Start device ping for ip '{}'. [timeout: {}, arpRetries: {}, arpTime: {}, sleepTime: {}]".format(self.ip_address,self.timeout,self.onlineArpRetries,self.onlineArpCheckTime,self.onlineSleepTime), flush=True)

        while self.isRunning:
            arpTime = self.onlineArpCheckTime if self.isOnline else self.offlineArpCheckTime
            arpRetries = self.onlineArpRetries if self.isOnline else self.offlineArpRetries
                
            startTime = datetime.now()
            changed = False
            
            loopIndex = 0
            while self.isRunning:
                if self.type != "android":
                    Helper.knock(self.address_family,self.ip_address)
                    time.sleep(0.05)
          
                cmd = ("/usr/sbin/arping -w {} -C 1 -i {} {}".format(arpTime,self.interface,self.ip_address)).split()
                process = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
                
                if process.returncode != 0 and self.isOnline:
                    print("Arping for {} was unsuccessful. Fallback to normal ping".format(self.ip_address), flush=True)
                    cmd = ("/bin/ping -c 1 {}".format(self.ip_address)).split()
                    process = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
                
                if process.returncode == 0:
                    print("Search for {} was successful after {} sec".format(self.ip_address,round((datetime.now() - startTime).total_seconds(),2)), flush=True)  
                    self.lastSeen = datetime.now()
                    if not self.isOnline:
                        self.isOnline = True
                        changed = True
                        print("Set {} to online".format(self.ip_address), flush=True)
                    break
                    
                loopIndex += 1
                if loopIndex == arpRetries:
                    print("Search for {} was unsuccessful".format(self.ip_address), flush=True)  
                    if self.isOnline:
                        self.isOnline = False
                        changed = True
                        print("Set {} to offline".format(self.ip_address), flush=True)
                    break
            
            if changed or (datetime.now() - self.lastPublished).total_seconds() > self.forcePublishTime:
                self.publish()

            sleepTime = self.onlineSleepTime if self.isOnline else self.offlineSleepTime
            time.sleep(sleepTime)
            
        print("Stop device ping for ip '{}'".format(self.ip_address), flush=True)
        
    def publish(self):
        self.lastPublished = datetime.now()
        self.mqtt_client.publish('device_ping/{}'.format(self.name), payload=("ON" if self.isOnline else "OFF"), qos=0, retain=False)
            
    def stop(self):
        if self.process != None:
            self.process.terminate()
        self.isRunning = False        
        #self.join()

class Handler(object):
    '''Handler client'''
    def __init__(self,interface):
        self.interface = interface

        self.devices = []

        self.mqtt_client = None
        self.dhcpListenerProcess = None
              
    def connectMqtt(self):
        print("Connection to mqtt ...", end='', flush=True)
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = lambda client, userdata, flags, rc: self.on_connect(client, userdata, flags, rc)
        self.mqtt_client.on_disconnect = lambda client, userdata, rc: self.on_disconnect(client, userdata, rc)
        self.mqtt_client.on_message = lambda client, userdata, msg: self.on_message(client, userdata, msg) 
        self.mqtt_client.connect("mosquitto", 1883, 60)
        print(" initialized", flush=True)
        
        self.mqtt_client.loop_start()
        
    def startDevicePing(self,devices):
        for device in devices:
            device = Device(device,devices[device],self.interface,self.mqtt_client)
            self.devices.append(device)
            device.start()
            
    def startDHCPListener(self):
        print("Start dhcp listener", flush=True)
        cmd = ("/usr/bin/stdbuf -oL /usr/bin/tcpdump -i {} -pvn port 67 or port 68".format(self.interface)).split()
        self.dhcpListenerProcess = subprocess.Popen( cmd,
                                                     bufsize=1,  # 0=unbuffered, 1=line-buffered, else buffer-size
                                                     universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT )

    def loop(self):        
        #status = os.fdopen(self.dhcpListenerProcess.stdout.fileno())
        #status = os.fdopen(os.dup(self.dhcpListenerProcess.stdout.fileno()))

        while True:
            output = self.dhcpListenerProcess.stdout.readline()
            self.dhcpListenerProcess.stdout.flush()
            if output == '' and self.dhcpListenerProcess.poll() is not None:
                print("Stopped dhcp listener", flush=True)
                break
            if output:
                line = output.strip()
                if line.startswith("Requested-IP"):
                    for device in self.devices:
                        if not device.isOnline and line.find(device.ip_address) != -1:
                            print("Triggered dhcp listener for ip '{}'".format(device.ip_address))
                            device.lastSeen = datetime.now()
                            device.isOnline = True
                            device.publish()
                            
        rc = self.dhcpListenerProcess.poll()

    def on_connect(self,client,userdata,flags,rc):
        print("Connected to mqtt with result code:"+str(rc), flush=True)
        
    def on_disconnect(self,client, userdata, rc):
        print("Disconnect from mqtt with result code:"+str(rc), flush=True)

    def on_message(self,client,userdata,msg):
        print("Topic " + msg.topic + ", message:" + str(msg.payload), flush=True)
            
    def terminate(self):
        if self.dhcpListenerProcess != None:
            print("Stop dhcp listener", flush=True)
            self.dhcpListenerProcess.terminate()

        for device in self.devices:
            device.stop()
            
        if self.mqtt_client != None:
            print("Close connection to mqtt", flush=True)
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
        
handler = Handler(interface)
handler.connectMqtt()

handler.startDevicePing(devices)
handler.startDHCPListener()

def cleanup(signum, frame):
    #print(signum)
    #print(frame)
    handler.terminate()
    exit(0)

signal.signal(signal.SIGTERM, cleanup)
signal.signal(signal.SIGINT, cleanup)

handler.loop()
