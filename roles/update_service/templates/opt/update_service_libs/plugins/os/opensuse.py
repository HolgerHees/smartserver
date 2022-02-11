import subprocess
import re
import sys

from plugins.os.os import Os


class OperatingSystem(Os):
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
          
    def getRebootState(self):
        result = subprocess.run([ "/usr/bin/zypper", "needs-rebooting" ], shell=False, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=None )
        return result.returncode != 0
