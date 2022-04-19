import glob
import os
import json
import pyinotify

from pathlib import Path

from config import config

from server.watcher import watcher


class DependencyWatcher(watcher.Watcher): 
    def __init__(self, system_update_watcher ):
        self.system_update_watcher = system_update_watcher
        
        self.outdated_roles = {}
        self.last_modified = self.getStartupTimestamp()

        self.initOutdatedRoles()
        
    def notifyChange(self, event):
        name = os.path.basename(event["pathname"])
        if event["mask"] & pyinotify.IN_CREATE:
            self.outdated_roles[name] = True
        else:
            del self.outdated_roles[name]
        self.postProcess()

    def initOutdatedRoles(self):
        outdated_roles = {}
        files = glob.glob("{}*".format(config.outdated_roles_state_dir))
        for filename in files:
            name = os.path.basename(filename)
            outdated_roles[name] = True
        self.outdated_roles = outdated_roles
        self.postProcess()
        
    def postProcess(self):
        self.last_modified = self.getNowAsTimestamp()
            
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
