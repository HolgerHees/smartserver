import urllib.request
import json

from helper.version import Version

from datetime import datetime

class Repository:
    API_BASE = "https://api.github.com/repos/"
    WEB_BASE = "https://github.com/"
    
    def __init__(self,plugin_config,global_config):
        self.access_token = global_config['github_access_token']
      
        self.project = plugin_config['project']
        self.pattern = plugin_config['pattern'] if 'pattern' in plugin_config else None
        
        if self.pattern != None:
            version = Version.parseVersionString(plugin_config['version'],self.pattern)
            if version != None:
                self.tag = plugin_config['version']
                self.current_version = version.getVersionString()
            else:
                raise Exception('Can\'t parse version \'{}\' with pattern \'{}\''.format(plugin_config['version'],self.pattern))
        else:
            self.tag = None
            self.current_version = plugin_config['version']
            
    def _requestData(self,url):
        req = urllib.request.Request(url)
        req.add_header('Authorization', "token {}".format(self.access_token))
        with urllib.request.urlopen(req) as response:
            raw = response.read().decode("utf-8") 
            return json.loads(raw)
        raise Exception('Something went wrong during fetching data from github project {}'.format(self.project))
      
    def _getUpdateUrl(self,tag = None):
        if tag != None:
            return "{}{}/releases/tag/{}".format(Repository.WEB_BASE,self.project,tag)
        else:
            return "{}{}/commits/master".format(Repository.WEB_BASE,self.project)

    def getCurrentBranch(self):
        return Version(self.current_version).getBranch() if self.tag != None else self.current_version

    def getCurrentVersion(self):
        commit_url = "{}{}/commits/{}".format(Repository.API_BASE,self.project,self.current_version if self.tag is None else self.tag)
        commit_data = self._requestData(commit_url)
        return { 'version': self.current_version, 'branch': self.getCurrentBranch(), 'date': commit_data['commit']['author']['date'], 'url': self._getUpdateUrl(self.tag) }

    def getUpdates(self, last_updates):
        new_updates_r = {}

        if self.pattern != None:
            current_updates_r = {}
            if last_updates is not None:
                for last_update in last_updates:
                    version = Version(last_update['version'])
                    current_updates_r[version.getBranch()] = [ version, last_update['date'], None ]
            
            current_version = Version(self.current_version)
        
            url = "{}{}/tags".format(Repository.API_BASE,self.project)
            data = self._requestData(url)
            
            for tag in data:
                version = Version.parseVersionString(tag['name'],self.pattern)
                if version is None:
                    continue
                  
                if version.getBranch() in current_updates_r and current_updates_r[version.getBranch()][2] is None:
                    current_updates_r[version.getBranch()][2] = tag['name']
                  
                if current_version.compare(version) == 1:
                    if version.getBranch() in current_updates_r and current_updates_r[version.getBranch()][0].compare(version) < 1:
                        continue

                    commit_url = tag['commit']['url']
                    commit_data = self._requestData(commit_url)

                    current_updates_r[version.getBranch()] = [ version, commit_data['commit']['author']['date'], tag['name'] ]
                        
            for branch in current_updates_r:
                version = current_updates_r[branch]
                new_updates_r[branch] = { 'version': version[0].getVersionString(), 'branch': branch, 'date': version[1], 'url': self._getUpdateUrl(version[2]) }

        else:
            current_update = None
            if last_updates is not None:
                for last_update in last_updates:
                    current_update = last_update
          
            total_commits = 0
            url = '{}{}/compare/{}...master'.format(Repository.API_BASE, self.project, self.current_version)
            data = self._requestData(url)
            
            total_commits = data['total_commits']
            if total_commits > 0:
                version = "{} commits".format(total_commits)
              
                if current_update != None and current_update['version'] == version:
                    new_updates_r['master'] = current_update
                else:                    
                    commit_url = '{}{}/commits/master'.format(Repository.API_BASE, self.project)
                    commit_data = self._requestData(commit_url)
                  
                    new_updates_r['master'] = { 'version': version, 'branch': 'master', 'date': commit_data['commit']['author']['date'], 'url': self._getUpdateUrl() }
                
        return new_updates_r
