import logging
import threading
import time
import os
import redis
import queue
import json
import threading
from datetime import datetime
import subprocess

from smartserver import inotify
from smartserver import command
from smartserver.metric import Metric

from lib._process import Process


class INotifyListener(threading.Thread):
    def __init__(self, config):
        threading.Thread.__init__(self)

        self.is_running = False
        self.config = config

        self.process = Process(self.config.cmd_inotify_listener)
        self.event = threading.Event()

    def start(self):
        self.is_running = True
        super().start()

    def terminate(self):
        if not self.is_running:
            return

        self.is_running = False

        self.event.set()
        self.process.terminate()
        self.process.join()

        self.join()

    def run(self):
        logging.info("INotify listener started")
        try:
            while self.is_running:
                #logging.info(str(self.config.cmd_inotify_listener))
                self.process.run(lambda msg: logging.info(msg))
                if self.process.hasErrors():
                    logging.info("Not able to run nextcloud '{}' app. Try again in 60 seconds".format(self.process.getApp()))
                    self.event.wait(60)
                    self.event.clear()
                elif self.process.isShutdown():
                    break

        except Exception as e:
            self.is_running = False
            raise e
        finally:
            logging.info("INotify listener stopped")

    def getStateMetrics(self):
        return [
            Metric.buildProcessMetric("nextcloud_service", "inotify_listener", "1" if self.is_running else "0"),
            Metric.buildStateMetric("nextcloud_service", "inotify_listener", "app", "1" if not self.process.hasErrors() else "0", { "app": self.process.getApp() })
        ]
