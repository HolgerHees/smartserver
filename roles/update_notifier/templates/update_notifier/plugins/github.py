from helper.version import Version

class Repository:
  
    def __init__(self,config):
        self.current_version = ""
                
    def getCurrentVersion(self):
        return self.current_version

    def getCurrentBranch(self):
        return Version(self.current_version).getBranch()

    def getNewVersions(self):
        new_version_r = {}
        return new_version_r
