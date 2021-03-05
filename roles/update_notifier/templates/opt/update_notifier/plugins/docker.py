import urllib.request
import json
import subprocess

from helper.version import Version

import re

from plugins.plugin import Plugin, SkipableVersionError

class Repository(Plugin):
    API_BASE = "https://registry-1.docker.io/v2/"
    WEB_BASE = "https://hub.docker.com/"

    repositories = None
  
    def __init__(self,plugin_config,global_config):
        self.repository = plugin_config['repository']
        if self.repository.find("/") == -1:
            self.repository = "library/{}".format(self.repository)

        self.pattern = plugin_config['pattern']
        
        if Repository.repositories is None:
            Repository.repositories = {}
            result = subprocess.run([ "/usr/bin/docker image list" ], shell=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=None )
            lines = result.stdout.decode("utf-8").split("\n")
            for line in lines:
                columns = line.split()
                if len(columns) == 0:
                    continue
                
                if columns[0] not in Repository.repositories:
                    Repository.repositories[columns[0]] = []

                Repository.repositories[columns[0]].append({'tag': columns[1],'image': columns[2]})
                

        data_r = Repository.repositories[plugin_config['repository']]
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
                return "{}_/{}?tab=tags&name={}".format(Repository.WEB_BASE,self.repository[8:],tag)
            else:
                return "{}r/{}/tags?name={}".format(Repository.WEB_BASE,self.repository,tag)
        else:
            return "{}r/{}/tags".format(Repository.WEB_BASE,self.repository)
          
    def _requestData(self,url,token=None,count=0):
        req = urllib.request.Request(url)
        if token != None:
            req.add_header('Authorization', "Bearer {}".format(token))

        raw = self.requestUrl(req)
        data = json.loads(raw)
        return data
      
    def _getCreationDate(self,tag):
        url = "{}{}/manifests/{}".format(Repository.API_BASE,self.repository,tag)
        image_data_r = self._requestData(url,self.token)
        for image_raw_data in image_data_r['history']:
            image_data = json.loads(image_raw_data['v1Compatibility'])
            date = re.sub("\.[0-9]+Z","Z",image_data['created'])
            return date
        raise Exception('No able to fetch creation date from docker repository {} and tag {}'.format(self.repository,tag))
          
    def getCurrentVersion(self):
        branch = Version(self.current_version).getBranchString()
        
        creationDate = self._getCreationDate(self.current_tag)
        return self.createUpdate( version = self.current_version, branch = branch, date = creationDate, url = self._getUpdateUrl(self.current_tag) )

    def getCurrentVersionString(self):
        return self.current_version

    def getUpdates(self, last_updates):
        current_version = Version(self.current_version)
        current_updates_r = self.filterPossibleVersions(current_version=current_version,last_updates=last_updates)
        
        url = "{}{}/tags/list".format(Repository.API_BASE,self.repository)
        data = self._requestData(url,self.token)
        
        for tag in data['tags']:
            version = Version.parseVersionString(tag,self.pattern)
            if version is None:
                continue
            
            self.updateCurrentUpdates(version=version,current_updates_r=current_updates_r,tag=tag)
            
            if self.isNewUpdate(version=version,current_updates_r=current_updates_r,current_version=current_version):
                try:
                    update_time = self._getCreationDate(tag)
                    self.registerNewUpdate(current_updates_r=current_updates_r, version=version, date=update_time, tag=tag )
                except SkipableVersionError as e:
                    pass

        new_updates_r = self.convertUpdates(current_updates_r=current_updates_r,project=self.repository)
        return new_updates_r

#print(data)
