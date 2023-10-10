import os
import time

from config import config

from server.watcher import watcher


class DeploymentTagsWatcher(watcher.Watcher): 
    def __init__(self):
        super().__init__()
        
        self.tags = []
        self.last_modified = self.getStartupTimestamp()
        
        self.initDeploymentTags(False)
        
    def notifyChange(self, event):
        self.initDeploymentTags(True)

    def initDeploymentTags(self,shouldRetry):
        self.tags = self.readJsonFile(config.deployment_tags_file,shouldRetry,[])
        self.last_modified = round(os.path.getmtime(config.deployment_tags_file) if os.path.exists(config.deployment_tags_file) else time.time(),3)
      
    def getLastModifiedAsTimestamp(self):
        return self.last_modified

    def getTags(self):
        return self.tags
