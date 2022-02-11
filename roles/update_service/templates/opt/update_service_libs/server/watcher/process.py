import threading
from datetime import datetime
import re
import sys

sys.path.insert(0, "/opt/shared/python")

from smartserver.processlist import Processlist


class ProcessWatcher(): 
    def __init__(self, logger, operating_system ):
        self.logger = logger
        
        self.reboot_required_services = []
        for string_pattern in operating_system.getRebootRequiredServices():
            regex_pattern = re.compile(string_pattern)
            self.reboot_required_services.append(regex_pattern)
            
        self.operating_system = operating_system
        
        self.is_running = True
        self.loop_counter = 0
        
        self.is_reboot_needed_by_core_update = False
        self.system_reboot_modified = 0
        
        self.is_reboot_needed_by_outdated_processes = False
        self.is_update_service_outdated = False
        self.outdated_services = []
        self.outdated_processes = {}
        self.oudated_processes_modified = 0
        
        self.condition = threading.Condition()
        self.thread = threading.Thread(target=self.checkProcesses, args=())
        self.thread.start()
        
    def terminate(self):
        with self.condition:
            self.is_running = False
            self.condition.notifyAll()
        
    def refresh(self):
        with self.condition:
            self.loop_iteration = 0
            self.condition.notifyAll()

    def cleanup(self):
        with self.condition:
            self.condition.notifyAll()

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
        self.outdated_services = services
        
        self.outdated_processes = outdated_processes
        
        self.is_update_service_outdated = is_update_service_outdated
        self.is_reboot_needed_by_outdated_processes = is_reboot_needed
        self.oudated_processes_modified = round(datetime.timestamp(datetime.now()),3)

    def checkProcesses(self):  
        with self.condition:
            while self.is_running:
                if self.loop_counter == 0:
                    self.logger.info("Refresh outdated processlist & reboot state")

                    is_reboot_needed_by_core_update = self.operating_system.getRebootState()
                    if self.is_reboot_needed_by_core_update != is_reboot_needed_by_core_update:
                        self.is_reboot_needed_by_core_update = is_reboot_needed_by_core_update
                        self.system_reboot_modified = round(datetime.timestamp(datetime.now()),3)

                    outdated_processes = Processlist.getOutdatedProcessIds()
                    if outdated_processes.keys() != self.outdated_processes.keys():
                        self.logger.info("new outdated processe(s)")
                        self.process(outdated_processes)
                    
                    self.loop_counter = 60 # => 15 min
                else:
                    #self.logger.info("clean outdated processlist")
                    if len(self.outdated_processes) > 0:    
                        #self.logger.info("sleep")
                        #self.logger.info("wakeup")

                        processIds = Processlist.getProcessIds()
                        outdated_processes = {k: v for k, v in self.outdated_processes.items() if k in processIds}
                        
                        if len(self.outdated_processes) != len(outdated_processes):
                            self.logger.info("{} outdated processe(s) cleaned".format( len(self.outdated_processes) - len(outdated_processes) ))
                            self.process(outdated_processes)

                self.loop_counter -= 1
                            
                self.condition.wait(15)
          
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
