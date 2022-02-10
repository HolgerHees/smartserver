import subprocess

from datetime import datetime

import re

from plugins.os.os import Os

sys.path.insert(0, "/opt/shared/python")

from smartserver.processlist import Processlist


class Repository(Os):
    DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
    HISTORY_FORMAT = "%Y-%m-%d %H:%M"
    VERSION_FORMAT = "%d.%m.%Y"
    
    def __init__(self):                              
        self.needs_restart = None
        self.outdated = None

    def getSystemUpdateCmd(self):
        return "/usr/bin/dnf update -y"

    def getRebootRequiredPackages(self):
        return []

    def getRebootRequiredServices(self):
        return []

    def getUpdates(self):
        result = subprocess.run([ "/usr/bin/dnf -y list updates" ], shell=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=None )
        lines = result.stdout.decode("utf-8").strip().split("\n")
        lines = reversed(lines)
        updates = []
        for line in lines:
            columns = re.sub(r"\s+", " ", line).split(" ")
            
            if len(columns) != 3:
                continue
              
            columns = [ele.strip() for ele in columns]
            
            name, arch = columns[0].rsplit('.', 1)
            
            updates.append({'repository': columns[2], 'name': name, 'current': None, 'update': columns[1], "arch": arch })

        return updates
      
    def __initSystemState__(self):
        result = subprocess.run([ "/usr/bin/needs-restarting -r" ], shell=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=None )
        self.needs_restart = result.returncode == 1
        
        self.outdated = Processlist.getOutdatedProcessIds()
        
    def getOutdatedProcesses(self):
        if self.outdated is None:
            self.__initSystemState__()
        return self.outdated
  
    def getRebootState(self):
        if self.needs_restart is None:
            self.__initSystemState__()
        return self.needs_restart

