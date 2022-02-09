from datetime import datetime

from config import config

from server.watcher import watcher


class SoftwareVersionWatcher(watcher.Watcher): 
    def __init__(self, logger ):
        super().__init__(logger)
      
        self.logger = logger
        
        self.software = {}
        self.last_modified = 0
        
        self.initSoftwareState(False)
        
    def notifyChange(self, event):
        self.initSoftwareState(True)
        
    def initSoftwareState(self, shouldRetry):
        self.software = self.readJsonFile(config.software_version_state_file,shouldRetry,{})
        self.last_modified = round(datetime.timestamp(datetime.now()),3)
        
    def getLastModifiedAsTimestamp(self):
        return self.last_modified
      
    def getSoftwareVersions(self):
        return self.software
