from config import config

from server.watcher import watcher


class SoftwareVersionWatcher(watcher.Watcher): 
    def __init__(self):
        super().__init__()
      
        self.software = {}
        self.update_count = 0
        self.last_modified = self.getStartupTimestamp()
        
        self.initSoftwareState(False)
        
    def notifyChange(self, event):
        self.initSoftwareState(True)
        
    def initSoftwareState(self, shouldRetry):
        self.software = self.readJsonFile(config.software_version_state_file,shouldRetry,{})
        self.update_count = 0
        if "states" in self.software:
            for state in self.software["states"]:
                if len(state["updates"]) > 0:
                    self.update_count += 1
        self.last_modified = self.getNowAsTimestamp()
        
    def getLastModifiedAsTimestamp(self):
        return self.last_modified
      
    def getSoftwareVersions(self):
        return self.software

    def getVersionCount(self):
        return self.update_count
