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

        self.is_running = True
        self.event = threading.Event()

        self.config = config
        self.handler = handler

        self.is_testing = False

        self.mqtt = mqtt
        self.influxdb = influxdb

        schedule.every().hour.at("00:00").do(self.startSpeedtest)
        #schedule.every(1).minutes.do(self.triggerSpeedtest)
        #self.triggerSpeedtest()

        self.influxdb.register(self.getMessurements)

        self.resetMetrics()

    def terminate(self):
        self.is_running = False
        self.event.set()

    def run(self):
        #max_retries = 20
        #while max_retries > 0:
        #    result = self.influxdb.get(["speedtest_upstream_rate","speedtest_downstream_rate","speedtest_ping"])
        #    if result is not None:
        #        logging.info("Initialize last data")
        #        self.resultUp = result["speedtest_upstream_rate"] if "speedtest_upstream_rate" in result else -1
        #        self.resultDown = result["speedtest_upstream_rate"] if "speedtest_downstream_rate" in result else -1
        #        self.resultPing = result["speedtest_upstream_rate"] if "speedtest_ping" in result else -1
        #        break

        #    logging.info("Last data not available. Retry in 15 seconds.")
        #    self.event.wait(15)

        #if max_retries == 0:
        #    logging.error("Not able to initialize last data.")

        try:
            while self.is_running:
                schedule.run_pending()

                self.event.wait(60)
                self.event.clear()
        except Exception:
            logging.error(traceback.format_exc())
            self.is_running = False

    def resetMetrics(self):
        self.resultUp = -1
        self.resultDown = -1
        self.resultPing = -1

    def triggerSpeedtest(self):
        t = threading.Thread(target=self.startSpeedtest, args=(0,), kwargs={})
        t.start()

    def startSpeedtest(self, retry = 3):
        if self.is_testing == True:
            return

        self.is_testing = True
        self.handler.notifySpeedtestData()

        messurements = []
        try:
            logging.info(u"Speedtest started")

            self.mqtt.publish("speedtest/time", "{:02d}:{:02d}".format(datetime.now().hour,datetime.now().minute))
            self.mqtt.publish("speedtest/location", "Aktiv")

            cmd = [ "/build/speedtest","-f", "json", "--accept-gdpr", "--accept-license" ]
            if self.config.speedtest_server_id != "auto":
                cmd.append("-s")
                cmd.append(self.config.speedtest_server_id)
            cmd.append("2>/dev/null")
            result = command.exec(cmd)
            json_string = result.stdout.decode("utf-8").strip()
            #json_string = '{"type":"result","timestamp":"2022-11-04T11:33:59Z","ping":{"jitter":0.059,"latency":1.356,"low":1.324,"high":1.425},"download":{"bandwidth":84670091,"bytes":415605496,"elapsed":4907,"latency":{"iqm":10.881,"low":1.791,"high":19.838,"jitter":2.385}},"upload":{"bandwidth":78355241,"bytes":684294663,"elapsed":8806,"latency":{"iqm":15.576,"low":2.088,"high":31.205,"jitter":1.839}},"packetLoss":0,"isp":"Internet bolaget Sverige AB","interface":{"internalIp":"192.168.0.50","name":"eth0","macAddr":"70:85:C2:F3:8A:30","isVpn":false,"externalIp":"185.89.36.59"},"server":{"id":30593,"host":"speed1.syseleven.net","port":8080,"name":"Inter.link GmbH","location":"Berlin","country":"Germany","ip":"37.49.159.242"},"result":{"id":"88ba990a-fb6f-44fa-bf64-5da183688778","url":"https://www.speedtest.net/result/c/88ba990a-fb6f-44fa-bf64-5da183688778","persisted":true}}'

            logging.info(u"Speedtest done")

            try:
                index = json_string.find("{\"type\":\"result\"")
                # fix to exclude license aggreement on first run
                if index != -1:
                    json_string = json_string[index:]

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

                self.resultUp = resultUp
                self.resultDown = resultDown
                self.resultPing = resultPing

                self.mqtt.publish("speedtest/upstream_rate", resultUp)
                self.mqtt.publish("speedtest/downstream_rate", resultDown)
                self.mqtt.publish("speedtest/ping", resultPing)

                messurements.append("speedtest_upstream_rate value={}".format(resultUp))
                messurements.append("speedtest_downstream_rate value={}".format(resultDown))
                messurements.append("speedtest_ping value={}".format(resultPing))
            except json.decoder.JSONDecodeError:
                self.resetMetrics()

                location = "Error"
                logging.error(u"Data error: {}".format(result))
        except Exception as e:
            self.resetMetrics()

            location = "Error"
            logging.error(traceback.format_exc())
        finally:
            if self.resultUp == -1 and retry > 0:
                if not self.event.is_set():
                    self.event.wait(60 - (retry * 15))

                    self.is_testing = False
                    self.startSpeedtest(retry - 1)
                return

            self.mqtt.publish("speedtest/time", "{:02d}:{:02d}".format(datetime.now().hour,datetime.now().minute))
            self.mqtt.publish("speedtest/location", location)

            messurements.append("speedtest_time value=\"{}\"".format("{:02d}:{:02d}".format(datetime.now().hour,datetime.now().minute)))
            messurements.append("speedtest_location value=\"{}\"".format(location))

            retry_count = 5
            while not self.event.is_set() and retry_count > 0:
                state = self.influxdb.submit(messurements)
                if state == 1:
                    break
                self.event.wait(self.config.influxdb_publish_interval)
                retry_count -= 1

            if retry_count == 0:
                logging.error("Maximum publish retries reached. Discard results now")

            self.is_testing = False

            self.handler.notifySpeedtestData()

    def getStateMetrics(self):
        metrics = []

        if self.resultUp != -1:
            metrics.append("system_service_speedtest{{type=\"upstream_rate\"}} {}".format(self.resultUp))
        if self.resultDown != -1:
            metrics.append("system_service_speedtest{{type=\"downstream_rate\"}} {}".format(self.resultDown))
        if self.resultPing != -1:
            metrics.append("system_service_speedtest{{type=\"ping\"}} {}".format(self.resultPing))

        metrics.append("system_service_process{{type=\"speedtest\",}} {}".format("1" if self.is_running else "0"))

        return metrics

    def getWebSocketData(self):
        return { "is_running": self.is_testing }

    def getMessurements(self):
        return []
