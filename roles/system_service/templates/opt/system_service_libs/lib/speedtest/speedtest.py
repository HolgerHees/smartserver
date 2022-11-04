#import netflow # https://github.com/bitkeks/python-netflow-v9-softflowd
import threading
import schedule
import traceback
import json
import requests

import logging

from datetime import datetime

from smartserver import command

class Speedtest(threading.Thread):
    def __init__(self, config, handler, mqtt, influxdb ):
        threading.Thread.__init__(self)

        #self.is_running = True
        self.event = threading.Event()

        self.config = config

        self.is_testing = False

        self.mqtt = mqtt
        self.influxdb = influxdb

        schedule.every().hour.at("00:00").do(self.startSpeedtest)
        #schedule.every(1).minutes.do(self.triggerSpeedtest)
        #self.triggerSpeedtest()

    def terminate(self):
        #self.is_running = False
        self.event.set()

    def run(self):
        while not self.event.is_set():
            schedule.run_pending()

            self.event.wait(60)
            #self.event.clear()

    def triggerSpeedtest(self):
        t = threading.Thread(target=self.startSpeedtest, args=(), kwargs={})
        t.start()

    def startSpeedtest(self):
        if self.is_testing == True:
            return

        self.is_testing = True

        try:
            logging.info(u"Speedtest started")

            self.mqtt.publish("speedtest/time", "{:02d}:{:02d}".format(datetime.now().hour,datetime.now().minute))
            self.mqtt.publish("speedtest/location", "Aktiv")

            result = command.exec([ "/build/speedtest","-f", "json", "--accept-gdpr", "--accept-license", "2>/dev/null" ] )
            json_string = result.stdout.decode("utf-8").strip()
            #json_string = '{"type":"result","timestamp":"2022-11-04T11:33:59Z","ping":{"jitter":0.059,"latency":1.356,"low":1.324,"high":1.425},"download":{"bandwidth":84670091,"bytes":415605496,"elapsed":4907,"latency":{"iqm":10.881,"low":1.791,"high":19.838,"jitter":2.385}},"upload":{"bandwidth":78355241,"bytes":684294663,"elapsed":8806,"latency":{"iqm":15.576,"low":2.088,"high":31.205,"jitter":1.839}},"packetLoss":0,"isp":"Internet bolaget Sverige AB","interface":{"internalIp":"192.168.0.50","name":"eth0","macAddr":"70:85:C2:F3:8A:30","isVpn":false,"externalIp":"185.89.36.59"},"server":{"id":30593,"host":"speed1.syseleven.net","port":8080,"name":"Inter.link GmbH","location":"Berlin","country":"Germany","ip":"37.49.159.242"},"result":{"id":"88ba990a-fb6f-44fa-bf64-5da183688778","url":"https://www.speedtest.net/result/c/88ba990a-fb6f-44fa-bf64-5da183688778","persisted":true}}'

            logging.info(u"Speedtest done")

            try:
                data = json.loads(json_string)

                resultPing = data["ping"]["latency"]
                resultDownBytes = data["download"]["bytes"]
                resultDownTime = data["download"]["elapsed"]
                resultDown = float(resultDownBytes) * 8 / 1024 / 1024 / ( float(resultDownTime) / 1000 )
                #resultDown = data["download.bandwidth"]
                resultUpBytes = data["upload"]["bytes"]
                resultUpTime = data["upload"]["elapsed"]
                resultUp = float(resultUpBytes) * 8 / 1024 / 1024 / ( float(resultUpTime) / 1000 )
                #resultUp = data["upload.bandwidth"]
                serverName = data["server"]["name"]
                serverLocation = data["server"]["location"]
                serverCountry = data["server"]["country"]

                location = "{} ({})".format(serverName,serverLocation)

                self.mqtt.publish("speedtest/upstream_rate", resultUp)
                self.mqtt.publish("speedtest/downstream_rate", resultDown)
                self.mqtt.publish("speedtest/ping", resultPing)

                messurements = [
                    "speedtest_upstream_rate value={}".format(resultUp),
                    "speedtest_downstream_rate value={}".format(resultDown),
                    "speedtest_ping value={}".format(resultPing)
                ]

                try:
                    self.influxdb.submit(messurements)
                except requests.exceptions.ConnectionError:
                    logging.info("InfluxDB currently not available")
            except json.decoder.JSONDecodeError:
                location = "Fehler"
                logging.error(u"Data error: {}".format(result))
        except Exception as e:
            location = "Fehler"
            logging.error(traceback.format_exc())
        finally:
            self.mqtt.publish("speedtest/time", "{:02d}:{:02d}".format(datetime.now().hour,datetime.now().minute))
            self.mqtt.publish("speedtest/location", location)
            self.is_testing = False
