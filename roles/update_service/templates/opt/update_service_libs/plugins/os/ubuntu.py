import subprocess
import re
import os

from plugins.os.os import Os

from smartserver import command


class OperatingSystem(Os):
    def getSystemUpdateCmds(self):
        return [ "/usr/bin/apt-get update -y", "/usr/bin/apt-get dist-upgrade -y" ]
      
    def getRebootRequiredPackages(self):
        return []

    def getRebootRequiredServices(self):
        return []

    def getUpdates(self):
        #apt list --upgradable
      
        result = command.exec([ "/usr/bin/apt", "list", "--upgradable" ])
        lines = result.stdout.decode("utf-8").strip().split("\n")
        updates = []
        for line in lines:
            columns = line.split(" ")
            
            #print(columns)
            #print(len(columns))
            
            if len(columns) != 6:
                continue
            
            name, repo = columns[0].split("/")
            _repo = repo.split(",")

            updates.append({'repository': _repo[0], 'name': name, 'current': columns[5][:-1], 'update': columns[1], "arch": columns[2] })

        return updates
          
    def getRebootState(self):
        return os.path.exists("/var/run/reboot-required")
            
