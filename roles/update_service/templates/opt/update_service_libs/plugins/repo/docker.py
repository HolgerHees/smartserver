import urllib.request
import json
import subprocess

from helper.version import Version

from smartserver import command

import re

from plugins.repo.app import App, SkipableVersionError

class Repository(object):
    def __init__(self,job_config,global_config):
        self.apps = [ Application(job_config,global_config) ]

    def getApplications(self):
        return self.apps

class Application(App):
    API_BASE = "https://registry-1.docker.io/v2/"
    WEB_BASE = "https://hub.docker.com/"

    repositories = None
  
    def __init__(self,job_config,global_config):
        super().__init__(job_config)

        self.plugin_config = job_config["config"]

    def checkForUpdates(self):

        self.repository = self.plugin_config['repository']
        if self.repository.find("/") == -1:
            self.repository = "library/{}".format(self.repository)

        self.pattern = self.plugin_config['pattern']
        
        if Application.repositories is None:
            Application.repositories = {}
            result = command.exec([ "/usr/bin/docker", "image", "list" ] )
            lines = result.stdout.decode("utf-8").split("\n")
            for line in lines:
                columns = line.split()
                if len(columns) == 0:
                    continue
                
                if columns[0] not in Application.repositories:
                    Application.repositories[columns[0]] = []

                Application.repositories[columns[0]].append({'tag': columns[1],'image': columns[2]})
                

        data_r = Application.repositories[self.plugin_config['repository']]
        version = None
        tag = None
        tag_r = []
        for data in data_r:
            _version = Version.parseVersionString(data['tag'],self.pattern)
            if _version is not None and (version is None or version.compare(_version) == 1):
                version = _version
                tag = data['tag']
            tag_r.append(data['tag'])

        if version:
            self.current_version = version.getVersionString()
            self.current_tag = tag
        else:
            raise Exception('Can\'t find current version with pattern \'{}\'. Available versions are {}'.format(self.pattern,tag_r))
              
        url = "https://auth.docker.io/token?service=registry.docker.io&scope=repository:{}:pull".format(self.repository)
        token_result = self._requestData(url)
        self.token = token_result['token']

    def _getUpdateUrl(self,tag = None):
        if tag != None:
            if self.repository.startswith("library/"):
                return "{}_/{}?tab=tags&name={}".format(Application.WEB_BASE,self.repository[8:],tag)
            else:
                return "{}r/{}/tags?name={}".format(Application.WEB_BASE,self.repository,tag)
        else:
            return "{}r/{}/tags".format(Application.WEB_BASE,self.repository)
          
    def _requestData(self,url,token=None,count=0):
        req = urllib.request.Request(url)
        if token != None:
            req.add_header('Authorization', "Bearer {}".format(token))

        raw = self._requestUrl(req)
        data = json.loads(raw)
        return data
      
    def _getCreationDate(self,tag):
        url = "{}{}/manifests/{}".format(Application.API_BASE,self.repository,tag)
        image_data_r = self._requestData(url,self.token)
        for image_raw_data in image_data_r['history']:
            image_data = json.loads(image_raw_data['v1Compatibility'])
            date = re.sub("\.[0-9]+Z","Z",image_data['created'])
            return date
        raise Exception('No able to fetch creation date from docker repository {} and tag {}'.format(self.repository,tag))
          
    def getCurrentVersion(self):
        branch = Version(self.current_version).getBranchString()
        
        try:
          creationDate = self._getCreationDate(self.current_tag)
        except SkipableVersionError as e:
          creationDate = "1970-01-01 00:00:00"

        return self._createUpdate( version = self.current_version, branch = branch, date = creationDate, url = self._getUpdateUrl(self.current_tag) )

    def getCurrentVersionString(self):
        return self.current_version

    def getUpdates(self, last_updates):
        current_version = Version(self.current_version)
        current_updates_r = self._filterPossibleVersions(current_version=current_version,last_updates=last_updates)
        
        url = "{}{}/tags/list".format(Application.API_BASE,self.repository)
        data = self._requestData(url,self.token)
        
        for tag in data['tags']:
            version = Version.parseVersionString(tag,self.pattern)
            if version is None:
                continue
            
            self._updateCurrentUpdates(version=version,current_updates_r=current_updates_r,tag=tag)
            
            if self._isNewUpdate(version=version,current_updates_r=current_updates_r,current_version=current_version):
                try:
                    update_time = self._getCreationDate(tag)
                    self._registerNewUpdate(current_updates_r=current_updates_r, version=version, date=update_time, tag=tag )
                except SkipableVersionError as e:
                    pass

        new_updates_r = self._convertUpdates(current_updates_r=current_updates_r,project=self.repository)
        return new_updates_r

#print(data)
