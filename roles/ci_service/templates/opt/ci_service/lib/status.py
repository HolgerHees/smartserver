import os
import logging
import json
import threading

from smartserver.confighelper import ConfigHelper
from smartserver.metric import Metric


class State():
    def __init__(self, config):
        self.version = 1
        self.dump_path = config.status_file
        self.valid_cache_file = False

        self.data = None

        self.lock = threading.Lock()

        self._restore()

    def terminate(self):
        if os.path.exists(self.dump_path):
            self._dump()

    def _restore(self):
        self.valid_cache_file, data = ConfigHelper.loadConfig(self.dump_path, self.version )
        if data is not None:
            self.data = data["data"]
            logging.info("Loaded state")
        else:
            self.data = { "status": None, "config": None, "deployment": None, "git_hash": None, "vid": None}
            self._dump()

    def _dump(self):
        if self.valid_cache_file:
            with self.lock:
                ConfigHelper.saveConfig(self.dump_path, self.version, { "data": self.data } )
                logging.info("Saved state")

    def save(self):
        self._dump()

    def setState(self, status):
        with self.lock:
            self.data["status"] = status

    def getState(self):
        return self.data["status"]

    def setDeployment(self, deployment):
        with self.lock:
            self.data["deployment"] = deployment

    def getDeployment(self):
        return self.data["deployment"]

    def setConfig(self, config):
        with self.lock:
            self.data["config"] = config

    def getConfig(self):
        return self.data["config"]

    def setGitHash(self, git_hash):
        with self.lock:
            self.data["git_hash"] = git_hash

    def getGitHash(self):
        return self.data["git_hash"]

    def setVID(self, vid):
        with self.lock:
            self.data["vid"] = vid

    def getVID(self):
        return self.data["vid"]

    def getStateMetrics(self):
        return [
            Metric.buildStateMetric("ci_service", "state", "cache_file", "1" if self.valid_cache_file else "0")
        ]

