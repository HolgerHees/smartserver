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
        with self.lockCmd([ "/usr/bin/needs-restarting", "-r" ]) as cmd:
            result = command.exec(cmd, exitstatus_check = False)
        return result.returncode == 1

    def getInstalledVersion(self, packagename ):
        result = command.exec([ "rpm -qi {} | grep -P \"Version\s*: \" | cut -d':' -f2- | xargs".format(packagename) ], shell=True, exitstatus_check = False )
        if result.returncode == 0:
            return result.stdout.decode("utf-8").strip()
        else:
            return 0
