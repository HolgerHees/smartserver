import abc

from helper.version import Version

class Plugin:
    def filterPossibleVersions(self,current_version,last_updates):
        current_updates_r = {}
        if last_updates is not None:
            for last_update in last_updates:
                version = Version(last_update['version'])
                if current_version.compare(version) < 1:
                    continue
                current_updates_r[version.getBranch()] = [ version, last_update['date'], None ]
        return current_updates_r

    def updateCurrentUpdates(self,version,current_updates_r,tag):
        if version.getBranch() in current_updates_r and current_updates_r[version.getBranch()][0].compare(version) == 0:
            current_updates_r[version.getBranch()][2] = tag

    def isNewUpdate(self,version,current_updates_r,current_version):
        if current_version.compare(version) == 1:
            if version.getBranch() in current_updates_r and current_updates_r[version.getBranch()][0].compare(version) < 1:
                return False
            print(current_updates_r)
            print(version)
            return True
        return False
    
    def registerNewUpdate(self,current_updates_r, version, date, tag):
        current_updates_r[version.getBranch()] = [ version, date, tag ]
        
    def convertUpdates(self,current_updates_r,project):
        new_updates_r = {}
        for branch in current_updates_r:
            version = current_updates_r[branch]
            if version[2] is None:
                raise Exception('Tag missing in version data in project {} version {}'.format(project,version[0].getVersionString()))
            new_updates_r[branch] = self.createUpdate( version = version[0].getVersionString(), branch = branch, date = version[1], url = self._getUpdateUrl(version[2]) )
        return new_updates_r
    
    def createUpdate(self,version,branch,date,url):
        return { 'version': version, 'branch': branch, 'date': date, 'url': url }
        
    @abc.abstractmethod
    def _getUpdateUrl(self,tag = None):
        return
