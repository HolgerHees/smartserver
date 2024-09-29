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
from smartserver.metric import Metric


class INotifyPublisher(threading.Thread):
    def __init__(self, config, preview_generator, handler):
        threading.Thread.__init__(self)

        self.is_running = False

        self.config = config
        self.preview_generator = preview_generator
        self.handler = handler

        self.event = threading.Event()

        self.redis = redis.Redis(host=config.redis_host, port=config.redis_port, db=0)

        self.rename_events = {}

        self.queue = queue.Queue()

    def start(self):
        self.is_running = True
        super().start()

    def terminate(self):
        if not self.is_running:
            return

        self.is_running = False

        self.event.set()

        self.join()

    def trigger(self, event, time):
        self.queue.put([event, time])
        self.event.set()

    def run(self):
        logging.info("INotify publisher started")
        try:
            while self.is_running:
                try:
                    event, time = self.queue.get_nowait()

                    time_as_iso = time.isoformat()

                    nextcloud_event = None
                    if event.mask & ( inotify.Constants.IN_MOVED_TO | inotify.Constants.IN_MOVED_FROM ):
                        if event.cookie not in self.rename_events:
                            self.rename_events[event.cookie] = {'event': 'move', 'from': None, 'to': None, 'time': None }

                        self.rename_events[event.cookie]['time'] = time_as_iso
                        self.rename_events[event.cookie]['from' if event.mask & inotify.Constants.IN_MOVED_FROM else 'to'] = event.path

                        if self.rename_events[event.cookie]['from'] is not None and self.rename_events[event.cookie]['to'] is not None:
                            nextcloud_event = self.rename_events[event.cookie]
                            del self.rename_events[event.cookie]
                    elif event.mask & inotify.Constants.IN_DELETE:
                        nextcloud_event = {'event': 'delete', 'path': event.path, 'time': time_as_iso}
                    elif event.mask & inotify.Constants.IN_CREATE:
                        nextcloud_event = {'event': 'modify', 'path': event.path, 'time': time_as_iso, 'size': 0}
                    elif event.mask & inotify.Constants.IN_CLOSE_WRITE:
                        try:
                            nextcloud_event = {'event': 'modify', 'path': event.path, 'time': time_as_iso, 'size': 0 if event.mask & inotify.Constants.IN_ISDIR else os.stat(event.path).st_size}
                        except FileNotFoundError:
                            # TODO maybe convert to a modify event, during follow up move event
                            # can happen when uploading *.part and rename after
                            continue
                    else:
                        logging.warn("Unexpected event: " + str(event))

                    if nextcloud_event is not None:
                        logging.info("PUBLISH: " + str( nextcloud_event))
                        self.redis.lpush("inotify", json.dumps(nextcloud_event))

                        self.preview_generator.trigger()

                    self.handler.confirmEvent(time)

                except queue.Empty:
                    #logging.info("Sleep queue loop")
                    self.event.wait()
                    self.event.clear()
        except Exception as e:
            self.is_running = False
            raise e
        finally:
            logging.info("INotify publisher stopped")

    def getStateMetrics(self):
        return [
            Metric.buildProcessMetric("nextcloud_service", "inotify_publisher", "1" if self.is_running else "0")
        ]
