from config import config

from server.watcher import watcher


class SoftwareVersionWatcher(watcher.Watcher): 
    def __init__(self):
        super().__init__()
      
        self.software = {}
        self.last_modified = self.getStartupTimestamp()
        
        self.initSoftwareState(False)
        
    def notifyChange(self, event):
        self.initSoftwareState(True)
        
    def initSoftwareState(self, shouldRetry):
        self.software = self.readJsonFile(config.software_version_state_file,shouldRetry,{})
        self.last_modified = self.getNowAsTimestamp()
        
    def getLastModifiedAsTimestamp(self):
        return self.last_modified
      
    def getSoftwareVersions(self):
        return self.software
