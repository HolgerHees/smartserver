import subprocess
import re

from plugins.os.os import Os

from smartserver import command

class OperatingSystem(Os):
    def getSystemUpdateCmds(self):
        return [ "/usr/bin/dnf update -y" ]

    def getRebootRequiredPackages(self):
        return []

    def getRebootRequiredServices(self):
        return []

    def getUpdates(self):
        result = command.exec([ "/usr/bin/dnf", "-y", "list updates" ])
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
      
    def getRebootState(self):
        result = command.exec([ "/usr/bin/needs-restarting", "-r" ], exitstatus_check = False)
        return result.returncode == 1
