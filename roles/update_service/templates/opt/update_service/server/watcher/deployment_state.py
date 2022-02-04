import os
import json
from datetime import datetime

from config import config


class DeploymentStateWatcher(): 
    def __init__(self, logger):
        self.logger = logger
        
        self.state = {}
        self.last_modified = 0
        
        self.initDeploymentState()
        
    def notifyChange(self, event):
        self.initDeploymentState()

    def initDeploymentState(self):
        self.state = {}
        if os.path.isfile(config.deployment_state_file):
            with open(config.deployment_state_file, 'r') as f:
                self.state = json.load(f)
        self.last_modified = round(datetime.timestamp(datetime.now()),3)
    
    def hasEncryptedValut(self):
        return self.state["has_encrypted_vault"] if "has_encrypted_vault" in self.state else False
      
    def getConfig(self):
        return self.state["config"] if "config" in self.state else None

    def getServer(self):
        return self.state["server"] if "server" in self.state else None

    def getLastModifiedAsTimestamp(self):
        return self.last_modified
