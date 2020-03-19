import urllib.request
import json

from helper.version import Version

from datetime import datetime

from plugins.plugin import Plugin

class Repository(Plugin):
    def __init__(self,plugin_config,global_config):

    def getCurrentBranch(self):
        pass

    def getCurrentVersion(self):
        pass

    def getCurrentVersionString(self):
        return ""

    def getUpdates(self, last_updates):
        new_updates_r = {}
        return new_updates_r
