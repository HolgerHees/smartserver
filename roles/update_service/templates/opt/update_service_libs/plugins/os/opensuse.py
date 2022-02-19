import subprocess
import re

from plugins.os.os import Os

from smartserver import command


class OperatingSystem(Os):
    def getSystemUpdateCmds(self):
        return [ "/usr/bin/zypper dup -y" ]
      
    def getRebootRequiredPackages(self):
        return ["wicked","wicked-service"]

    def getRebootRequiredServices(self):
        return [r"^wicked.*$"]

    def getUpdates(self):
        result = command.exec([ "/usr/bin/zypper", "list-updates" ])
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
          
    def getRebootState(self):
        result = command.exec([ "/usr/bin/zypper", "needs-rebooting" ], exitstatus_check = False)
        return result.returncode != 0
