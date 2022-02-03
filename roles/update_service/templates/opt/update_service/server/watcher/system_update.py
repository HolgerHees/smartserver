import os
import json
from datetime import datetime
from dateutil.parser import parse

from config import config

from server.watcher.process import ProcessWatcher


class SystemUpdateWatcher(): 
    def __init__(self, logger, process_watcher, reboot_required_packages ):
        self.logger = logger
        self.process_watcher = process_watcher
        self.reboot_required_packages = reboot_required_packages
        
        self.states = {}
        self.system_state_last_modified = 0
        self.system_update_last_modified = 0
        self.smartserver_update_last_modified = 0
        
        self.installed_reboot_required_packages = {}
        
        self.initSystemState()
        
    def notifyChange(self,event):
        self.initSystemState()

    def initSystemState(self):
        if os.path.isfile(config.system_update_state_file):
            with open(config.system_update_state_file, 'r') as f:
                _states = json.load(f)
                                       
                if "system_updates" in self.states:
                    new_updates = {}
                    if "system_updates" in _states:
                        for update in _states["system_updates"]:
                            new_updates[update["name"]] = True
                    
                    for update in self.states["system_updates"]:
                        if update["name"] not in new_updates and update["name"] in self.reboot_required_packages:
                            self.installed_reboot_required_packages[update["name"]] = True
                
                self.states = _states
                self.system_state_last_modified = round(datetime.timestamp(parse(self.states["last_system_state"])),3)
                self.system_update_last_modified = round(datetime.timestamp(parse(self.states["last_system_update"])),3)
                self.smartserver_changes_last_modified = round(datetime.timestamp(parse(self.states["last_smartserver_update"])),3)
                self.smartserver_pull = round(datetime.timestamp(parse(self.states["smartserver_pull"])),3)

        self.process_watcher.initOutdatedProcesses(self.states["system_processes_outdated"])
        
    def getSystemStateLastModifiedAsTimestamp(self):
        return self.system_state_last_modified
      
    def isRebootNeeded(self):
        return self.isRebootNeededByOs() or self.isRebootNeededByOutdatedProcesses() or self.isRebootNeededByInstalledPackages()
        
    def isRebootNeededByOs(self):
        return self.states["system_reboot_needed"] if "system_reboot_needed" in self.states else False
      
    def isRebootNeededByInstalledPackages(self):
        return len(self.installed_reboot_required_packages) > 0
      
    def isRebootNeededByOutdatedProcesses(self):
        return self.process_watcher.isRebootNeeded()

    def getSystemUpdatesLastModifiedAsTimestamp(self):
        return self.system_update_last_modified

    def getSystemUpdates(self):
        return self.states["system_updates"] if "system_updates" in self.states else []
      
    def getSmartserverChangesLastModifiedAsTimestamp(self):
        return self.smartserver_changes_last_modified

    def getSmartserverChanges(self):
        return self.states["smartserver_changes"] if "smartserver_changes" in self.states else []
      
    def getSmartserverCode(self):
        return self.states["smartserver_code"] if "smartserver_code" in self.states else []
      
    def getSmartserverPullAsTimestamp(self):
        return self.smartserver_pull
