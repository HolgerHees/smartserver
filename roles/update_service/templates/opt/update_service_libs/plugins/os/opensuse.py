import subprocess
import re
import sys

from plugins.os.os import Os

sys.path.insert(0, "/opt/shared/python")

from smartserver.processlist import Processlist


class Repository(Os):
    DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
    HISTORY_FORMAT = "%Y-%m-%d %H:%M:%S"
    VERSION_FORMAT = "%d.%m.%Y"
  
    def __init__(self):          
        self.needs_restart = None
        self.outdated = None

    def getSystemUpdateCmd(self):
        return "/usr/bin/zypper dup -y"
      
    def getRebootRequiredPackages(self):
        return ["wicked","wicked-service"]

    def getRebootRequiredServices(self):
        return [r"^wicked.*$"]

    def getUpdates(self):
        result = subprocess.run([ "/usr/bin/zypper list-updates" ], shell=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=None )
        lines = result.stdout.decode("utf-8").strip().split("\n")
        lines = reversed(lines)
        updates = []
        for line in lines:
            columns = line.split(" | ")
            if len(columns) < 5:
                break
            columns = [ele.strip() for ele in columns]
            updates.append({'repository': columns[1], 'name': columns[2], 'current': columns[3], 'update': columns[4], 'arch': columns[5] })

        return updates
          
    def __initSystemState__(self):
        result = subprocess.run([ "/usr/bin/zypper", "needs-rebooting" ], shell=False, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=None )
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
            
