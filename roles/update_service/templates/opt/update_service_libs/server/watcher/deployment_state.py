from datetime import datetime

from config import config

from server.watcher import watcher


class DeploymentStateWatcher(watcher.Watcher): 
    def __init__(self, logger):
        super().__init__(logger)
        
        self.logger = logger
        
        self.state = {}
        self.last_modified = 0
        
        self.initDeploymentState(False)
        
    def notifyChange(self, event):
        self.initDeploymentState(True)

    def initDeploymentState(self,shouldRetry):
        self.state = self.readJsonFile(config.deployment_state_file,shouldRetry,{})
        self.last_modified = round(datetime.timestamp(datetime.now()),3)
    
    def hasEncryptedValut(self):
        return self.state["has_encrypted_vault"] if "has_encrypted_vault" in self.state else False
      
    def getConfig(self):
        return self.state["config"] if "config" in self.state else None

    def getServer(self):
        return self.state["server"] if "server" in self.state else None

    def getLastModifiedAsTimestamp(self):
        return self.last_modified
