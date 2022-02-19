import threading
from datetime import datetime, timedelta
import re

from smartserver.processlist import Processlist

from server.watcher import watcher

class ProcessWatcher(watcher.Watcher): 
    def __init__(self, logger, operating_system ):
        super().__init__(logger)
      
        self.logger = logger
        
        self.reboot_required_services = []
        for string_pattern in operating_system.getRebootRequiredServices():
            regex_pattern = re.compile(string_pattern)
            self.reboot_required_services.append(regex_pattern)
            
        self.operating_system = operating_system
        
        self.is_running = True
        self.last_refresh = datetime.now() - timedelta(hours=24) # to force a full refresh
        
        self.is_reboot_needed_by_core_update = False
        self.system_reboot_modified = self.getStartupTimestamp()
        
        self.is_reboot_needed_by_outdated_processes = False
        self.is_update_service_outdated = False
        self.outdated_services = []
        self.outdated_processes = {}
        self.oudated_processes_modified = self.getStartupTimestamp()
        
        self.condition = threading.Condition()
        self.thread = threading.Thread(target=self.checkProcesses, args=())
        self.thread.start()
        
    def process(self, outdated_processes):
        is_reboot_needed = False
        for pid in outdated_processes:
            service = outdated_processes[pid]["service"]
            if service == "":
                is_reboot_needed = True
                break
            else:
                for regex_pattern in self.reboot_required_services:
                    if regex_pattern.match(service):
                        is_reboot_needed = True
                        break
                     
        is_update_service_outdated = False
        services = []
        for pid in outdated_processes:
            service = outdated_processes[pid]["service"]
            if not service:
                continue
            if service == "update_service":
                is_update_service_outdated = True
            services.append(service)
        self.outdated_services = list(set(services))
        
        self.outdated_processes = outdated_processes
        
        self.is_update_service_outdated = is_update_service_outdated
        self.is_reboot_needed_by_outdated_processes = is_reboot_needed
        self.oudated_processes_modified = self.getNowAsTimestamp()

    def checkProcesses(self):  
        with self.condition:
            while self.is_running:
                if ( datetime.now() - self.last_refresh ).total_seconds() > 900:
                    self._refresh()
                else:
                    #self.logger.info("clean outdated processlist")
                    self._cleanup()

                self.condition.wait(15)
        
    def terminate(self):
        with self.condition:
            self.is_running = False
            self.condition.notifyAll()
        
    def refresh(self):
        with self.condition:
            self._refresh()

    def cleanup(self):
        with self.condition:
            self._cleanup()

    def _refresh(self):
        self.logger.info("Refresh outdated processlist & reboot state")

        is_reboot_needed_by_core_update = self.operating_system.getRebootState()
        if self.is_reboot_needed_by_core_update != is_reboot_needed_by_core_update:
            self.is_reboot_needed_by_core_update = is_reboot_needed_by_core_update
            self.system_reboot_modified = self.getNowAsTimestamp()

        outdated_processes = Processlist.getOutdatedProcessIds()
        if outdated_processes.keys() != self.outdated_processes.keys():
            self.logger.info("new outdated processe(s)")
            self.process(outdated_processes)

        self.last_refresh = datetime.now()
        
    def _cleanup(self):
        if len(self.outdated_processes) == 0:    
            return
          
        processIds = Processlist.getProcessIds()
        outdated_processes = {k: v for k, v in self.outdated_processes.items() if k in processIds}
        
        if len(self.outdated_processes) != len(outdated_processes):
            self.logger.info("{} outdated processe(s) cleaned".format( len(self.outdated_processes) - len(outdated_processes) ))
            self.process(outdated_processes)

          
    def getOudatedProcesses(self):
        return list(self.outdated_processes.values())
      
    def getOutdatedServices(self):
        return self.outdated_services
      
    def isUpdateServiceOutdated(self):
        return self.is_update_service_outdated

    def isRebootNeededByCoreUpdate(self):
        return self.is_reboot_needed_by_core_update

    def isRebootNeededByOutdatedProcesses(self):
        return self.is_reboot_needed_by_outdated_processes
      
    def getOutdatedProcessesLastModifiedAsTimestamp(self):
        return self.oudated_processes_modified

    def getSystemRebootLastModifiedAsTimestamp(self):
        return self.system_reboot_modified

    def getLastRefreshAsTimestamp(self):
        return round(datetime.timestamp(self.last_refresh),3)
