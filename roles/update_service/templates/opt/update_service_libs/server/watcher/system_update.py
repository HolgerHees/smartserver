from datetime import datetime

from config import config

from server.watcher.process import ProcessWatcher

from server.watcher import watcher


class SystemUpdateWatcher(watcher.Watcher): 
    def __init__(self, logger, process_watcher, reboot_required_packages ):
        super().__init__(logger)
      
        self.logger = logger
        self.process_watcher = process_watcher
        self.reboot_required_packages = reboot_required_packages
        
        self.states = {}
        self.system_state_last_modified = 0
        self.system_update_last_modified = 0
        self.smartserver_changes_last_modified = 0
        self.smartserver_pull = 0
        
        self.installed_reboot_required_packages = {}
        
        self.initSystemState(False)
        
    def notifyChange(self, event):
        self.initSystemState(True)
        
    def parseTime(self, datetimeStr):
        datetimeStr = "{}{}".format(datetimeStr[0:-3],datetimeStr[-2:])
        datetimeObj = datetime.strptime(datetimeStr,"%Y-%m-%dT%H:%M:%S.%f%z")
        timestamp = round(datetime.timestamp(datetimeObj),3)
        return timestamp

    def initSystemState(self,shouldRetry):
        _states = self.readJsonFile(config.system_update_state_file,shouldRetry,{})
        if len(_states) > 0:
            if "system_updates" in self.states:
                new_updates = {}
                if "system_updates" in _states:
                    for update in _states["system_updates"]:
                        new_updates[update["name"]] = True
                
                for update in self.states["system_updates"]:
                    if update["name"] not in new_updates and update["name"] in self.reboot_required_packages:
                        self.logger.info("Found packages '{}' which is marked as 'requires reboot'".format(update["name"]))
                        self.installed_reboot_required_packages[update["name"]] = True
            
            self.states = _states
            #2022-02-04T03:30:02.059664+01:00
            self.system_state_last_modified = self.parseTime(self.states["last_system_state"])
            self.system_update_last_modified = self.parseTime(self.states["last_system_update"])
            self.smartserver_changes_last_modified = self.parseTime(self.states["last_smartserver_update"])
            self.smartserver_pull = self.parseTime(self.states["smartserver_pull"]) if self.states["smartserver_pull"] else ""
            #self.system_state_last_modified = round(datetime.timestamp(parse(self.states["last_system_state"])),3)
            #self.system_update_last_modified = round(datetime.timestamp(parse(self.states["last_system_update"])),3)
            #self.smartserver_changes_last_modified = round(datetime.timestamp(parse(self.states["last_smartserver_update"])),3)
            #self.smartserver_pull = round(datetime.timestamp(parse(self.states["smartserver_pull"])),3)

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
        return self.states["smartserver_code"] if "smartserver_code" in self.states else ""
      
    def getSmartserverPullAsTimestamp(self):
        return self.smartserver_pull
