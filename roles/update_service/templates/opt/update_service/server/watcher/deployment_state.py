from config import config

from server.watcher import watcher


class DeploymentStateWatcher(watcher.Watcher): 
    def __init__(self):
        super().__init__()
        
        self.state = {}
        self.last_modified = self.getStartupTimestamp()
        
        self.initDeploymentState(False)
        
    def notifyChange(self, event):
        self.initDeploymentState(True)

    def initDeploymentState(self,shouldRetry):
        self.state = self.readJsonFile(config.deployment_state_file,shouldRetry,{})
        self.last_modified = self.getNowAsTimestamp()
    
    def hasEncryptedVault(self):
        return self.state["has_encrypted_vault"] if "has_encrypted_vault" in self.state else False
      
    def getLastModifiedAsTimestamp(self):
        return self.last_modified
