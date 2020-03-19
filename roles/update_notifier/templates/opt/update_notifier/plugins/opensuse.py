import urllib.request
import json

from helper.version import Version

from datetime import datetime

from plugins.plugin import Plugin

class Repository(Plugin):
    '''
    >>>zypper lu
    Repository-Daten werden geladen...
    Installierte Pakete werden gelesen...
    S | Repository             | Name   | Aktuelle Version  | Verfügbare Version | Arch  
    --+------------------------+--------+-------------------+--------------------+-------
    v | Main Update Repository | dracut | 044.2-lp151.2.9.1 | 044.2-lp151.2.12.1 | x86_64
    v | Main Update Repository | pam    | 1.3.0-lp151.8.3.1 | 1.3.0-lp151.8.6.1  | x86_64

    >>>zypper lu
    Repository-Daten werden geladen...
    Installierte Pakete werden gelesen...
    Keine Aktualisierungen gefunden.
    '''
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
