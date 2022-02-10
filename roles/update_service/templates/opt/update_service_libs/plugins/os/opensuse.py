import subprocess
import re
import sys

from datetime import datetime

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
        result = subprocess.run([ "/usr/bin/zypper ps -s" ], shell=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=None )
        result = result.stdout.decode("utf-8").strip()
        lines = result.split("\n")
        
        # Ein Neustart wird benötigt, um sicher zu stellen, dass ihr System von diesen Updates profitiert.
        m = re.search('(?!.*nicht).*[Nn]eustart.*|(?!.*not).*[Rr]eboot.*', lines[-1])
        self.needs_restart = m is not None
        
        # PID   | PPID  | UID | User     | Command          | Service
        # ------+-------+-----+----------+------------------+-----------------
        # 1     | 0     | 0   | root     | systemd          | 
        # 409   | 1     | 0   | root     | systemd-journald | systemd-journald
        outdated = []
        for line in lines:
            if "|" not in line:
                continue
            columns = line.split("|")
            columns = [ele.strip() for ele in columns]
            if not columns[0].isnumeric():
                continue
            
            outdated.append({"pid": columns[0], "ppid": columns[1], "uid": columns[2], "user": columns[3], "command": columns[4], "service": columns[5]})
        self.outdated = outdated
        
        _outdated = Processlist.getOutdatedProcessIds()
        
        if len(self.outdated) != len(_outdated):
            print(self.outdated)
            print(_outdated)
            raise Exception("Different outdated processes detected")
        else:
            for process in self.outdated:
                found = False
                for _process in _outdated:
                    if process["pid"] == _process["pid"]:
                        found = True
                        break
                if not found:
                    print(self.outdated)
                    print(_outdated)
                    raise Exception("Process '{}' not match in outdated processes".format(process["pid"]))

    def getOutdatedProcesses(self):
        if self.outdated is None:
            self.__initSystemState__()
        return self.outdated
  
    def getRebootState(self):
        if self.needs_restart is None:
            self.__initSystemState__()
        return self.needs_restart
            
