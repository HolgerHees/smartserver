import urllib.request
import json
from datetime import datetime

from smartserver import command

from helper.version import Version

from plugins.repo.app import App

class Repository(object):
    def __init__(self,job_config,global_config):
        #self.apps = [ Application(job_config,global_config) ]
        result = command.exec([ "docker","exec", "php", "sh", "-c", "php /dataDisk/htdocs/nextcloud/occ app:list" ] )
        lines = result.stdout.decode("utf-8").split("\n")
        current_versions = {}
        for line in lines:
            columns = line.split()
            if len(columns) == 0 or columns[0] != "-":
                continue
            current_versions[columns[1][:-1]] = columns[-1]

        #print(current_versions)

        self.apps = []
        result = command.exec([ "docker","exec", "php", "sh", "-c", "php /dataDisk/htdocs/nextcloud/occ app:update --showonly" ] )
        lines = result.stdout.decode("utf-8").split("\n")
        for line in lines:
            columns = line.split()
            if len(columns) == 0:
                continue
            self.apps.append(Application(columns[0], columns[-1], current_versions[columns[0]], job_config['url']))

    def getApplications(self):
        return self.apps


class Application(App):
    def __init__(self,name, new_version, current_version, base_url):
        #super().__init__(job_config)
        self.name = name
        self.type = "nextcloud"
        self.url = "{}{}".format(base_url, self.name)

        self.current_version = current_version
        self.new_version = new_version

    def checkForUpdates(self):
        pass

    def getName(self):
        return "nextcloud_{}".format(self.name)

    def getType(self):
        return self.type

    def getUrl(self):
        return self.url

    def getCurrentVersion(self):
        branch = Version(self.current_version).getBranchString()
        date = "{}".format(datetime.now().astimezone().isoformat())
        return self._createUpdate( version = self.current_version, branch = branch, date = date, url = self.url )

    def getCurrentVersionString(self):
        return self.current_version

    def getCurrentVersionString(self):
        return self.getCurrentVersionString

    def getUpdates(self, last_updates):
        branch = Version(self.new_version).getBranchString()
        date = "{}".format(datetime.now().astimezone().isoformat())

        return { branch: self._createUpdate( version = self.new_version, branch = branch, date = date, url = self.url ) }
