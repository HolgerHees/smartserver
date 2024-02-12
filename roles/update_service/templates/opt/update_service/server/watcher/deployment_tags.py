from config import config

from server.watcher import watcher


class DeploymentTagsWatcher(watcher.Watcher): 
    def __init__(self, handler):
        super().__init__()
        
        self.handler = handler

        self.tags = []
        
        self.initDeploymentTags(False)
        
    def notifyChange(self, event):
        self.initDeploymentTags(True)
        self.handler.notifyWatcherTagState()

    def initDeploymentTags(self,shouldRetry):
        self.tags = self.readJsonFile(config.deployment_tags_file,shouldRetry,[])
      
    def getTags(self):
        return self.tags
