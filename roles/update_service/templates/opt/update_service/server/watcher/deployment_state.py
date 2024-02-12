from config import config

from server.watcher import watcher


class DeploymentStateWatcher(watcher.Watcher): 
    def __init__(self, handler):
        super().__init__()
        
        self.handler = handler

        self.state = {}

        self.initDeploymentState(False)
        
    def notifyChange(self, event):
        self.initDeploymentState(True)
        self.handler.notifyWatcherDeploymentState()

    def initDeploymentState(self,shouldRetry):
        self.state = self.readJsonFile(config.deployment_state_file,shouldRetry,{})
    
    def hasEncryptedVault(self):
        return self.state["has_encrypted_vault"] if "has_encrypted_vault" in self.state else False
