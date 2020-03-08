import urllib.request
import json
import subprocess

from datetime import datetime

from helper.version import Version

import http.client

import time

import re

class Repository:
  
    REGISTRY = "https://registry-1.docker.io/v2/"
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
                Repository.repositories[columns[0]] = {'tag': columns[1],'image': columns[2]}

        data = Repository.repositories[plugin_config['repository']]
        version = Version.parseVersionString(data['tag'],self.pattern)
        if version:
            self.current_version = version.getVersionString()
            self.current_tag = data['tag']
        else:
            raise Exception('Can\'t parse version \'{}\' with pattern \'{}\''.format(data['tag'],self.pattern))
              
        url = "https://auth.docker.io/token?service=registry.docker.io&scope=repository:{}:pull".format(self.repository)
        token_result = self._requestData(url)
        self.token = token_result['token']

    def _getUpdateUrl(self,tag):
        return "{}r/{}/tags?name={}".format(Repository.REGISTRY,self.repository,tag)
          
    def _requestData(self,url,token=None,count=0):
        req = urllib.request.Request(url)
        if token != None:
            req.add_header('Authorization', "Bearer {}".format(token))
        with urllib.request.urlopen(req) as response:
            try:
                raw = response.read().decode("utf-8")
            except (http.client.IncompleteRead) as e:
                if count > 5:
                    raise Exception('More then 5 retries to fetch data from docker repository {} and tag {}'.format(self.repository,tag))
                time.sleep(10)
                return self._requestData(url,token,count+1)
            data = json.loads(raw)
            return data
        raise Exception('Something went wrong during fetching data from docker repository {} and tag {}'.format(self.repository,tag))
      
    def _getCreationDate(self,tag):
        url = "{}{}/manifests/{}".format(Repository.REGISTRY,self.repository,tag)
        image_data_r = self._requestData(url,self.token)
        for image_raw_data in image_data_r['history']:
            image_data = json.loads(image_raw_data['v1Compatibility'])
            date = re.sub("\.[0-9]+Z","Z",image_data['created'])
            return date
        raise Exception('No able to fetch creation date from docker repository {} and tag {}'.format(self.repository,tag))
          
    def getCurrentBranch(self):
        return Version(self.current_version).getBranch()

    def getCurrentVersion(self):
        update_time = self._getCreationDate(self.current_tag)
        return { 'version': self.current_version, 'branch': self.getCurrentBranch(), 'date': update_time, 'url': self._getUpdateUrl(self.current_tag) }

    def getUpdates(self, last_updates):
        current_version = Version(self.current_version)

        current_updates_r = {}
        if last_updates is not None:
            for last_update in last_updates:
                version = Version(last_update['version'])
                current_updates_r[version.getBranch()] = [ version, last_update['date'], None ]
        
        url = "{}{}/tags/list".format(Repository.REGISTRY,self.repository)
        data = self._requestData(url,self.token)
        
        for tag in data['tags']:
            version = Version.parseVersionString(tag,self.pattern)
            if version is None:
                continue
              
            if version.getBranch() in current_updates_r and current_updates_r[version.getBranch()][2] is None:
                current_updates_r[version.getBranch()][2] = tag
            
            if current_version.compare(version) == 1:
                if version.getBranch() in current_updates_r and current_updates_r[version.getBranch()][0].compare(version) < 1:
                    continue
                  
                update_time = self._getCreationDate(tag)
                current_updates_r[version.getBranch()] = [ version, update_time, tag ]
                    
        new_updates_r = {}
        for branch in current_updates_r:
            version = current_updates_r[branch]
            new_updates_r[branch] = { 'version': version[0].getVersionString(), 'branch': branch, 'date': version[1], 'url': self._getUpdateUrl(version[2]) }
                  
        return new_updates_r

#print(data)
