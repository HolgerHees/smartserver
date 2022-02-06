import os
import json
from datetime import datetime

from config import config

class SoftwareVersionWatcher(): 
    def __init__(self, logger ):
        self.logger = logger
        
        self.software = {}
        self.last_modified = 0
        
        self.initSoftwareState()
        
    def notifyChange(self, event):
        self.initSoftwareState()
        
    def initSoftwareState(self):
        if os.path.isfile(config.software_version_state_file):
            with open(config.software_version_state_file, 'r') as f:
                self.software = json.load(f)
                self.last_modified = round(datetime.timestamp(datetime.now()),3)
        
    def getLastModifiedAsTimestamp(self):
        return self.last_modified
      
    def getSoftwareVersions(self):
        return self.software
