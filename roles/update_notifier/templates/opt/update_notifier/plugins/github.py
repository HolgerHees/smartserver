import urllib.request
import json

from helper.version import Version

from plugins.plugin import Plugin

class Repository(Plugin):
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
        if self.access_token:
            req.add_header('Authorization', "token {}".format(self.access_token))
        
        raw = self.requestUrl(req)
        return json.loads(raw)
      
    def _getUpdateUrl(self,tag = None):
        if tag != None:
            return "{}{}/releases/tag/{}".format(Repository.WEB_BASE,self.project,tag)
        else:
            return "{}{}/commits/master".format(Repository.WEB_BASE,self.project)

    def getCurrentVersion(self):
        branch = Version(self.current_version).getBranchString() if self.tag != None else 'master'
    
        commit_url = "{}{}/commits/{}".format(Repository.API_BASE,self.project,self.current_version if self.tag is None else self.tag)
        commit_data = self._requestData(commit_url)
        return self.createUpdate( version = self.current_version, branch = branch, date = commit_data['commit']['author']['date'], url = self._getUpdateUrl(self.tag) )

    def getCurrentVersionString(self):
        return self.current_version

    def getUpdates(self, last_updates):
        new_updates_r = {}

        if self.pattern != None:
            current_version = Version(self.current_version)
            current_updates_r = self.filterPossibleVersions(current_version=current_version,last_updates=last_updates)
            
            url = "{}{}/tags".format(Repository.API_BASE,self.project)
            data = self._requestData(url)
            
            for tag in data:
                version = Version.parseVersionString(tag['name'],self.pattern)
                if version is None:
                    continue
                  
                self.updateCurrentUpdates(version=version,current_updates_r=current_updates_r,tag=tag['name'])
                  
                if self.isNewUpdate(version=version,current_updates_r=current_updates_r,current_version=current_version):
                    commit_data = self._requestData(tag['commit']['url'])
                    self.registerNewUpdate(current_updates_r=current_updates_r, version=version, date=commit_data['commit']['author']['date'], tag=tag['name'])

            new_updates_r = self.convertUpdates(current_updates_r=current_updates_r,project=self.project)

        else:
            current_update = last_updates[0] if last_updates is not None and len(last_updates) > 0 else None
          
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
                  
                    new_updates_r['master'] = self.createUpdate( version = version, branch = 'master', date = commit_data['commit']['author']['date'], url = self._getUpdateUrl() )
                
        return new_updates_r
