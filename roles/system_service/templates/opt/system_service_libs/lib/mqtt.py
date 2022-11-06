import paho.mqtt.client as mqtt
import logging


class MQTTHandler():
    def __init__(self, config):
        self.mqtt_client = None
        self.config = config

    def start(self):
        while True:
            try:
                logging.info("Connection to mqtt ...")
                self.mqtt_client = mqtt.Client()
                self.mqtt_client.on_connect = lambda client, userdata, flags, rc: self.on_connect(client, userdata, flags, rc)
                self.mqtt_client.on_disconnect = lambda client, userdata, rc: self.on_disconnect(client, userdata, rc)
                self.mqtt_client.on_message = lambda client, userdata, msg: self.on_message(client, userdata, msg)
                self.mqtt_client.connect(self.config.mqtt_host, 1883, 60)

                self.mqtt_client.loop_start()
                break
            except Exception as e:
                logging.info("MQTT {}. Retry in 5 seconds".format(str(e)))
                time.sleep(self.config.startup_error_timeout)

    def on_connect(self,client,userdata,flags,rc):
        logging.info("Connected to mqtt with result code:"+str(rc))

    def on_disconnect(self,client, userdata, rc):
        logging.info("Disconnect from mqtt with result code:"+str(rc))

    def on_message(self,client,userdata,msg):
        logging.info("Topic " + msg.topic + ", message:" + str(msg.payload))

    def publish(self, name, payload):
        self.mqtt_client.publish('system_info/{}'.format(name), payload=payload, qos=0, retain=False)

    def terminate(self):
        if self.mqtt_client is not None:
            logging.info("Close connection to mqtt")
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()

