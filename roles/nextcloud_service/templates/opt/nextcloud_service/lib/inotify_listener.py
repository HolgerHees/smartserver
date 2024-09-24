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


class INotifyListener(threading.Thread):
    def __init__(self, config):
        threading.Thread.__init__(self)

        self.event = threading.Event()

        self.is_running = False
        self.config = config

        self.app_state = -1

    def start(self):
        self.is_running = True
        super().start()

    def terminate(self):
        if self.is_running:
            self.is_running = False

            self.event.set()
            self.join()

    def run(self):
        logging.info("INotify listener started")
        try:
            while self.is_running:
                #logging.info(str(self.config.cmd_inotify_listener))
                process = command.popen(self.config.cmd_inotify_listener, run_on_host=True)
                os.set_blocking(process.stdout.fileno(), False)
                start = time.time()
                while self.is_running and process.poll() is None:
                    for line in iter(process.stdout.readline, b''):
                        if line == '':
                            break
                        logging.info("RECEIVED: " + line.strip())
                    if self.app_state != 1 and time.time() - start > 5:
                        self.app_state = 1
                    time.sleep(0.5)
                if not self.is_running:
                    process.terminate()
                    break
                else:
                    self.app_state = 0
                    logging.info("Not able to run nextcloud 'inotify listener' app. Try again in 60 seconds.")
                    self.event.wait(60)
                    self.event.clear()
                    if self.is_running:
                        logging.info("Restart inotify listener")

        except Exception as e:
            self.is_running = False
            raise e
        finally:
            logging.info("INotify listener stopped")

    def getStateMetrics(self):
        metrics = [
            "nextcloud_service_process{{type=\"inotify_listener\",group=\"main\"}} {}".format("1" if self.is_running else "0"),
            "nextcloud_service_process{{type=\"inotify_listener\",group=\"app\",details=\"files_notify_redis:primary\"}} {}".format(self.app_state)
        ]
        return metrics
