import logging
import threading
import time
import os

from smartserver import command
from smartserver.metric import Metric

from lib._process import Process


class PreviewGenerator(threading.Thread):
    def __init__(self, config):
        threading.Thread.__init__(self)

        self.is_running = False
        self.config = config

        self.process = Process(self.config.cmd_preview_generator)
        self.event = threading.Event()

        self.first_event = 0
        self.last_event = 0

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

    def trigger(self):
        self.last_event = time.time()
        if self.first_event == 0:
            self.first_event = self.last_event
        self.event.set()

    def run(self):
        logging.info("Preview generator started")
        self.event.clear()
        try:
            while self.is_running:
                now = time.time()
                next_timeout = self.config.min_preview_delay - (now - self.last_event)
                max_timeout = self.config.max_preview_delay - (now - self.first_event)
                timeout = min(next_timeout, max_timeout)
                if timeout <= 0:
                    runtime = self.process.run(lambda msg: logging.info(msg), silent=True)
                    if self.process.hasErrors():
                        logging.info("Not able to run nextcloud '{}' app. Try again in 60 seconds".format(self.process.getApp()))
                        self.event.wait(60)
                    else:
                        if not self.is_running or self.process.isShutdown():
                            break
                        logging.info("Previews generated in {:.2f} seconds".format(runtime))
                        self.first_event = self.last_event = 0
                        self.event.wait()
                else:
                    self.event.wait(timeout)
                self.event.clear()
        except Exception as e:
            self.is_running = False
            raise e
        finally:
            logging.info("Preview generator stopped")

    def getStateMetrics(self):
        return [
            Metric.buildProcessMetric("nextcloud_service", "preview_generator", "1" if self.is_running else "0"),
            Metric.buildStateMetric("nextcloud_service", "inotify_listener", "app", "1" if not self.process.hasErrors() else "0", { "app": self.process.getApp() })
        ]
