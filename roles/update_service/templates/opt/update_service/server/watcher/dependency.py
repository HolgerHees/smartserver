import glob
import os
import json
from datetime import datetime

from config import config


class DependencyWatcher(): 
    def __init__(self, logger, system_update_watcher ):
        self.logger = logger
        
        self.system_update_watcher = system_update_watcher
        
        self.outdated_roles = {}
        self.last_modified = 0

        self.initOutdatedRoles()
        
    def notifyChange(self,event):
        name = os.path.basename(event.pathname)
        if event.maskname == "IN_CREATE":
            self.outdated_roles[name] = True
        else:
            del self.outdated_roles[name]
        self.initOutdatedRoles()

    def initOutdatedRoles(self):
        self.outdated_roles = {}
        files = glob.glob("{}*".format(config.outdated_roles_state_dir))
        for filename in files:
            name = os.path.basename(filename)
            self.outdated_roles[name] = True
        self.last_modified = round(datetime.timestamp(datetime.now()),3)
            
    def getOutdatedRoles(self):
        return list(self.outdated_roles.keys())
            
    def getLastModifiedAsTimestamp(self):
        return self.last_modified
      
    def checkSmartserverRoles(self):
        files = glob.glob("{}*.conf".format(config.dependencies_config_dir))
        package_tag_map = {}
        for config_file in files:
            with open(config_file) as json_data:
                dependency_config = json.load(json_data)
                for package in dependency_config["packages"]:
                    if package not in package_tag_map:
                        package_tag_map[package] = []
                    package_tag_map[package].append(dependency_config["tag"])
        
        system_updates = self.system_update_watcher.getSystemUpdates()
        for update in system_updates:
            for package in package_tag_map:
                if package == update["name"]:
                    for tag in package_tag_map[package]:
                        f = Path(u"{}{}".format(config.outdated_roles_state_dir,tag))
                        f.touch(exist_ok=True)
