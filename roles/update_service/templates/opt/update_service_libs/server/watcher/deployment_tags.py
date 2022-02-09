from datetime import datetime

from config import config

from server.watcher import watcher


class DeploymentTagsWatcher(watcher.Watcher): 
    def __init__(self, logger):
        super().__init__(logger)
      
        self.logger = logger
        
        self.tags = []
        self.last_modified = 0
        
        self.initDeploymentTags(False)
        
    def notifyChange(self, event):
        self.initDeploymentTags(True)

    def initDeploymentTags(self,shouldRetry):
        self.tags = self.readJsonFile(config.deployment_tags_file,shouldRetry,[])
        self.last_modified = round(datetime.timestamp(datetime.now()),3)
      
    def getLastModifiedAsTimestamp(self):
        return self.last_modified

    def getTags(self):
        return self.tags
