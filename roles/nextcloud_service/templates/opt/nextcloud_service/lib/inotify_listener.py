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

from lib._process import Process


class INotifyListener(threading.Thread):
    def __init__(self, config):
        threading.Thread.__init__(self)

        self.listener_process = Process()
        self.listener_event = threading.Event()

        self.is_running = False
        self.config = config

    def start(self):
        self.is_running = True
        super().start()

    def terminate(self):
        if not self.is_running:
            return

        self.is_running = False

        self.listener_event.set()
        self.listener_process.terminate()
        self.listener_process.join()

        self.join()

    def run(self):
        logging.info("INotify listener started")
        try:
            while self.is_running:
                #logging.info(str(self.config.cmd_inotify_listener))
                self.listener_process.run(self.config.cmd_inotify_listener, lambda msg: logging.info("RECEIVED: " + msg))
                if self.listener_process.hasErrors():
                    logging.info("Not able to run nextcloud 'inotify listener' app. Try again in 60 seconds.")
                    self.listener_event.wait(60)
                    self.listener_event.clear()
                    if self.is_running:
                        logging.info("Restart inotify listener")
                elif self.listener_process.isShutdown():
                    break

        except Exception as e:
            self.is_running = False
            raise e
        finally:
            logging.info("INotify listener stopped")

    def getStateMetrics(self):
        metrics = [
            "nextcloud_service_process{{type=\"inotify_listener\",group=\"main\"}} {}".format("1" if self.is_running else "0"),
            "nextcloud_service_process{{type=\"inotify_listener\",group=\"app\",details=\"files_notify_redis:primary\"}} {}".format("1" if not self.listener_process.hasErrors() else "0")
        ]
        return metrics
