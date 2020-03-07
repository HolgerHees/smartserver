import urllib.request
import json

from helper.version import Version

class Repository:
    #https://api.github.com/repos/netdata/netdata/tags
    #https://api.github.com/repos/netdata/netdata/commits/523d6747c3443322460fbedd65b502c25317f2dd
    #https://api.github.com/repos/netdata/netdata
  
    
    #https://github.com/netdata/netdata/tags
    
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
                
    def _getUpdateUrl(self,tag = None):
        if tag != None:
            return "{}{}/releases/tag/{}".format(Repository.WEB_BASE,self.project,tag)
        else:
            return "{}{}/commits/master".format(Repository.WEB_BASE,self.project)

    def getCurrentBranch(self):
        return Version(self.current_version).getBranch() if self.tag != None else self.current_version

    def getCurrentVersion(self):
        return { 'version': self.current_version, 'url': self._getUpdateUrl(self.tag) }

    def getNewVersions(self):
      
        new_version_r = {}

        if self.pattern != None:
            current_version = Version(self.current_version)
        
            last_version_r = {}
            
            url = "{}{}/tags".format(Repository.API_BASE,self.project)
            
            req = urllib.request.Request(url)
            req.add_header('Authorization', "token {}".format(self.access_token))
            with urllib.request.urlopen(req) as response:
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
                        
            for branch in last_version_r:
                new_version_r[branch] = { 'version': last_version_r[branch][0].getVersionString(), 'url': self._getUpdateUrl(last_version_r[branch][1]) }

        else:
          
            total_commits = 0
            url = '{}{}/compare/{}...master'.format(Repository.API_BASE, self.project, self.current_version)
            req = urllib.request.Request(url)
            req.add_header('Authorization', "token {}".format(self.access_token))
            with urllib.request.urlopen(req) as response:
                raw = response.read().decode("utf-8")
                data = json.loads(raw)
                
                total_commits = data['total_commits']
                
            if total_commits > 0:
                new_version_r['master'] = { 'version': "{} commits".format(total_commits), 'url': self._getUpdateUrl() }
                #url = '{}{}/commits'.format(Repository.API_BASE, self.project)
                #req = urllib.request.Request(url)
                #req.add_header('Authorization', "token {}".format(self.access_token))
                #with urllib.request.urlopen(req) as response:

                #   raw = response.read().decode("utf-8")
                #    data = json.loads(raw)

        return new_version_r
