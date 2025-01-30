import glob
import os
import json
import re
import logging

from pathlib import Path

from config import config

from server.watcher import watcher

from smartserver.filewatcher import FileWatcher


class DependencyWatcher(watcher.Watcher): 
    def __init__(self, handler, system_update_watcher ):
        self.handler = handler
        self.system_update_watcher = system_update_watcher
        
        self.outdated_roles = {}

        self.initOutdatedRoles()
        
    def notifyChange(self, event):
        if event["type"] not in [FileWatcher.EVENT_TYPE_CREATED, FileWatcher.EVENT_TYPE_MOVED_TO, FileWatcher.EVENT_TYPE_MOVED_FROM, FileWatcher.EVENT_TYPE_DELETED]:
            return

        name = os.path.basename(event["path"])
        if event["type"] in [FileWatcher.EVENT_TYPE_CREATED, FileWatcher.EVENT_TYPE_MOVED_TO]:
            self.outdated_roles[name] = True
        else:
            del self.outdated_roles[name]

        self.handler.notifyWatcherDependencyState()

    def initOutdatedRoles(self):
        outdated_roles = {}
        files = glob.glob("{}*".format(config.outdated_roles_state_dir))
        for filename in files:
            name = os.path.basename(filename)
            outdated_roles[name] = True
        self.outdated_roles = outdated_roles
            
    def getOutdatedRoles(self):
        return list(self.outdated_roles.keys())
            
    def checkSmartserverSystemUpdateDependedRoles(self):
        files = glob.glob("{}*.conf".format(config.dependencies_config_dir))
        package_tag_map = {}
        for config_file in files:
            with open(config_file) as json_data:
                dependency_config = json.load(json_data)
                if "packages" not in dependency_config:
                    continue

                for package in dependency_config["packages"]:
                    if package not in package_tag_map:
                        package_tag_map[package] = { "regex": re.compile(package, re.IGNORECASE), "tags": [] }
                    package_tag_map[package]["tags"].append(dependency_config["tag"])
        
        system_updates = self.system_update_watcher.getSystemUpdates()
        for update in system_updates:
            for package in package_tag_map:
                if not package_tag_map[package]["regex"].match(update["name"]):
                    continue

                self._touchOutdatedRole(package_tag_map[package]["tags"])

    def checkSmartserverSmartserverUpdateDependedRoles(self, tags):
        files = glob.glob("{}*.conf".format(config.dependencies_config_dir))
        for config_file in files:
            with open(config_file) as json_data:
                dependency_config = json.load(json_data)
                if "roles" not in dependency_config:
                    continue

                if len(tags) == 0:
                    self._touchOutdatedRole(dependency_config["tag"])
                    continue

                for role in dependency_config["roles"]:
                    if role not in tags:
                        continue
                    self._touchOutdatedRole(dependency_config["tag"])
                    continue

    def _touchOutdatedRole(self, tag):
        f = Path(u"{}{}".format(config.outdated_roles_state_dir,tag))
        f.touch(exist_ok=True)
