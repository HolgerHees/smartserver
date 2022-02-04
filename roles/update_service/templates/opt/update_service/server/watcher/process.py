import threading
import subprocess
from datetime import datetime

class ProcessWatcher(): 
    def __init__(self, logger ):
        self.logger = logger
        
        self.is_reboot_needed = False
        self.outdated_processes = {}
        self.last_modified = 0
        
        self.condition = threading.Condition()
        self.thread = threading.Thread(target=self.checkProcesses, args=())
        self.thread.start()
        
        
    def initOutdatedProcesses(self,outdated_processes):
        for state in outdated_processes:
            self.outdated_processes[state["pid"]] = state

        if len(self.outdated_processes) > 0:
            with self.condition:
                self.condition.notifyAll()
        else:
            self.checkRebootRequired()
            self.last_modified = round(datetime.timestamp(datetime.now()),3)
            
    def checkRebootRequired(self):
        is_reboot_needed = False
        for process in self.outdated_processes:
            if process["service"] == "":
                is_reboot_needed = True
                break
        self.is_reboot_needed = is_reboot_needed

    def checkProcesses(self):  
        #processes = self.getProcesslist()
        #self.logger.info(processes)
        with self.condition:
            while True:
                if len(self.outdated_processes) > 0:    
                    self.logger.info("process")

                    self.logger.info(self.outdated_processes)

                    processes = self.getProcesslist()
                    self.outdated_processes = {k: v for k, v in self.outdated_processes.items() if k in processes}
                    
                    self.checkRebootRequired()
                    self.last_modified = round(datetime.timestamp(datetime.now()),3)
                    
                    self.condition.wait(15)
                else:
                    self.logger.info("sleep")
                    self.condition.wait()
                    self.logger.info("wakeup")
          
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
      
    def isRebootNeeded(self):
        return self.is_reboot_needed
      
    def getLastModifiedAsTimestamp(self):
        return self.last_modified

