import urllib.request
import json
import subprocess

from helper.version import Version

class Repository:
  
    REGISTRY="https://hub.docker.com/"
    repositories = None
  
    def __init__(self,plugin_config,global_config):
        self.repository = plugin_config['repository']
        self.pattern = plugin_config['pattern']
        self.url = "{}v1/repositories/{}/tags".format(Repository.REGISTRY,self.repository)
        
        if Repository.repositories is None:
            Repository.repositories = {}
            result = subprocess.run([ "/usr/bin/docker image list" ], shell=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=None )
            lines = result.stdout.decode("utf-8").split("\n")
            for line in lines:
                columns = line.split()
                if len(columns) == 0:
                    continue
                Repository.repositories[columns[0]] = {'tag': columns[1],'image': columns[2]}

        data = Repository.repositories[self.repository]
        version = Version.parseVersionString(data['tag'],self.pattern)
        if version:
            self.current_version = version.getVersionString()
            self.current_tag = data['tag']
        else:
            raise Exception('Can\'t parse version \'{}\' with pattern \'{}\''.format(data['tag'],self.pattern))
              
    def _getUpdateUrl(self,tag):
        
        if self.repository.find("/") == -1:
            return "{}_/{}?tab=tags&name={}".format(Repository.REGISTRY,self.repository,tag)
        else:
            return "{}r/{}/tags?name={}".format(Repository.REGISTRY,self.repository,tag)
    
    def getCurrentBranch(self):
        return Version(self.current_version).getBranch()

    def getCurrentVersion(self):
        return { 'version': self.current_version, 'url': self._getUpdateUrl(self.current_tag) }

    def getNewVersions(self):
        current_version = Version(self.current_version)

        last_version_r = {}

        with urllib.request.urlopen(self.url) as response:
            raw = response.read().decode("utf-8")

            data = json.loads(raw)
            
            for tag in data:
                version = Version.parseVersionString(tag['name'],self.pattern)
                if version is None:
                    continue
                
                if current_version.compare(version) == 1:
                    if version.getBranch() in last_version_r and last_version_r[version.getBranch()][0].compare(version) == -1:
                        continue

                    last_version_r[version.getBranch()] = [ version, tag['name'] ]
                    
        new_version_r = {}
        for branch in last_version_r:
            new_version_r[branch] = { 'version': last_version_r[branch][0].getVersionString(), 'url': self._getUpdateUrl(last_version_r[branch][1]) }
                  
        return new_version_r

#print(data)
