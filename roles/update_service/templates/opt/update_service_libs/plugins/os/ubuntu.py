import subprocess
import re
import sys
import os

from plugins.os.os import Os

sys.path.insert(0, "/opt/shared/python")

from smartserver.processlist import Processlist


class Repository(Os):
    def __init__(self):          
        self.needs_restart = None
        self.outdated = None

    def getSystemUpdateCmd(self):
        return "apt-get upgrade"
      
    def getRebootRequiredPackages(self):
        return []

    def getRebootRequiredServices(self):
        return []

    def getUpdates(self):
        #apt list --upgradable
      
        result = subprocess.run([ "/usr/bin/apt list --upgradable" ], shell=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=None )
        lines = result.stdout.decode("utf-8").strip().split("\n")
        updates = []
        for line in lines:
            columns = line.split(" ")
            
            #print(columns)
            #print(len(columns))
            
            if len(columns) != 4:
                continue
            
            name, repo = columns[0].split("/")
            _repo = repo.split(",")

            updates.append({'repository': _repo[0], 'name': name, 'current': None, 'update': columns[1], "arch": columns[2] })

        #print(updates)

        return updates
          
    def __initSystemState__(self):
        self.needs_restart = os.path.exists("/var/run/reboot-required")
        
        self.outdated = Processlist.getOutdatedProcessIds()

    def getOutdatedProcesses(self):
        if self.outdated is None:
            self.__initSystemState__()
        return self.outdated
  
    def getRebootState(self):
        if self.needs_restart is None:
            self.__initSystemState__()
        return self.needs_restart
            
