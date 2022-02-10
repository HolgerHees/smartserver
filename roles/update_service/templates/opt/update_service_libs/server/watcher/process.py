import threading
from datetime import datetime
import re
import sys

sys.path.insert(0, "/opt/shared/python")

from smartserver.processlist import Processlist


class ProcessWatcher(): 
    def __init__(self, logger, reboot_required_services ):
        self.logger = logger
        
        self.reboot_required_services = []
        for string_pattern in reboot_required_services:
            regex_pattern = re.compile(string_pattern)
            self.reboot_required_services.append(regex_pattern)
        
        self.is_running = True
        
        self.is_reboot_needed = False
        self.is_update_service_outdated = False
        self.outdated_services = []
        self.outdated_processes = {}
        self.last_modified = 0
        
        self.condition = threading.Condition()
        self.thread = threading.Thread(target=self.checkProcesses, args=())
        self.thread.start()
        
    def terminate(self):
        self.is_running = False
        with self.condition:
            self.condition.notifyAll()
        
    def initOutdatedProcesses(self,outdated_processes):
        _outdated_processes = {}
        for state in outdated_processes:
            _outdated_processes[state["pid"]] = state
            
        self.process(_outdated_processes, True)
            
    def process(self, outdated_processes, force):
      
        processIds = Processlist.getProcessIds()
        _outdated_processes = {k: v for k, v in outdated_processes.items() if k in processIds}
        
        if len(outdated_processes) != len(_outdated_processes):
            self.logger.info("{} outdated processe(s) cleaned".format( len(outdated_processes) - len(_outdated_processes) ))
            outdated_processes = _outdated_processes
        elif not force:
            return
                        
        is_reboot_needed = False
        for index in outdated_processes:
            service = outdated_processes[index]["service"]
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
        for index in outdated_processes:
            service = outdated_processes[index]["service"]
            if not service:
                continue
            if service == "update_service":
                is_update_service_outdated = True
            services.append(service)
        self.outdated_services = services
        
        self.outdated_processes = outdated_processes
        
        self.is_update_service_outdated = is_update_service_outdated
        self.is_reboot_needed = is_reboot_needed
        self.last_modified = round(datetime.timestamp(datetime.now()),3)

    def checkProcesses(self):  
        with self.condition:
            while self.is_running:
                if len(self.outdated_processes) > 0:    
                    #self.logger.info("sleep")
                    self.condition.wait(15)
                    #self.logger.info("wakeup")

                    self.process(self.outdated_processes, False)
                else:
                    #self.logger.info("sleep")
                    self.condition.wait()
                    #self.logger.info("wakeup")
          
    def getOudatedProcesses(self):
        return list(self.outdated_processes.values())
      
    def getOutdatedServices(self):
        return self.outdated_services
      
    def isUpdateServiceOutdated(self):
        return self.is_update_service_outdated

    def isRebootNeeded(self):
        return self.is_reboot_needed
      
    def getLastModifiedAsTimestamp(self):
        return self.last_modified

