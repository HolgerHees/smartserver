import os
import json
from datetime import datetime

from config import config


class DeploymentTagsWatcher(): 
    def __init__(self, logger):
        self.logger = logger
        
        self.tags = []
        self.last_modified = 0
        
        self.initDeploymentTags()
        
    def notifyChange(self, path, mask):
        self.initDeploymentTags()

    def initDeploymentTags(self):
        self.tags = []
        if os.path.isfile(config.deployment_tags_file):
            with open(config.deployment_tags_file, 'r') as f:
                self.tags = json.load(f)
        self.last_modified = round(datetime.timestamp(datetime.now()),3)
      
    def getLastModifiedAsTimestamp(self):
        return self.last_modified

    def getTags(self):
        return self.tags
