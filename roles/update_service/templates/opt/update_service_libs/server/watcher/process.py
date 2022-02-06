import threading
import subprocess
from datetime import datetime
import re
import time

class ProcessWatcher(): 
    def __init__(self, logger, reboot_required_services ):
        self.logger = logger
        
        self.reboot_required_services = []
        for string_pattern in reboot_required_services:
            regex_pattern = re.compile(string_pattern)
            self.reboot_required_services.append(regex_pattern)
        
        self.is_running = True
        
        self.is_reboot_needed = False
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
        for state in outdated_processes:
            self.outdated_processes[state["pid"]] = state
            
        if len(self.outdated_processes) > 0:
            with self.condition:
                self.condition.notifyAll()
        else:
            #self.outdated_processes["123"] = {"pid": 1, "ppid": 123, "uuid": "hhees", "cmd": "wickedd", "service": "testwickedd-auto"}

            self.postProcess()
            
    def postProcess(self):
        is_reboot_needed = False
        for index in self.outdated_processes:
            service = self.outdated_processes[index]["service"]
            if service == "":
                is_reboot_needed = True
                break
            else:
                for regex_pattern in self.reboot_required_services:
                    if regex_pattern.match(service):
                        is_reboot_needed = True
                        break
                      
        services = []
        for line in self.outdated_processes:
            if not line["service"]:
                continue
            services.append(line["service"])
        self.outdated_services = services
        
        self.is_reboot_needed = is_reboot_needed
        self.last_modified = round(datetime.timestamp(datetime.now()),3)

    def checkProcesses(self):  
        #processes = self.getProcesslist()
        #self.logger.info(processes)
        with self.condition:
            while self.is_running:
                if len(self.outdated_processes) > 0:    
                    #self.logger.info("process")

                    processes = self.getProcesslist()
                    _outdated_processes = {k: v for k, v in self.outdated_processes.items() if k in processes}
                    
                    if len(_outdated_processes) != len(self.outdated_processes):
                        self.logger.info("{} outdated processe(s) cleaned".format( len(self.outdated_processes) - len(_outdated_processes) ))
                        
                        self.outdated_processes = _outdated_processes
                        
                        self.postProcess()

                    #self.logger.info("sleep")
                    self.condition.wait(15)
                else:
                    #self.logger.info("sleep")
                    self.condition.wait()
                    #self.logger.info("wakeup")
          
    def getProcesslist(self):
        result = subprocess.run([ "ps", "-xo", "pid,ppid" ], shell=False, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT )
        result = result.stdout.decode("utf-8")
        lines = result.split("\n")
        result = {}
        for line in lines:
            if not line:
               continue
            
            columns = line.split(" ")
            columns = [column for column in columns if column ]
            result[columns[0]] = columns[1]
        return result
      
    def getOudatedProcesses(self):
        return list(self.outdated_processes.values())
      
    def getOutdatedServices(self):
        return self.outdated_services
      
    def isRebootNeeded(self):
        return self.is_reboot_needed
      
    def getLastModifiedAsTimestamp(self):
        return self.last_modified

