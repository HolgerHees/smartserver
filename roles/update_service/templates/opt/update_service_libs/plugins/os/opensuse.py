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







        result = subprocess.run([ "/usr/bin/zypper ps -s" ], shell=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=None )
        result = result.stdout.decode("utf-8").strip()
        lines = result.split("\n")
        
        # Ein Neustart wird benötigt, um sicher zu stellen, dass ihr System von diesen Updates profitiert.
        #m = re.search('(?!.*nicht).*[Nn]eustart.*|(?!.*not).*[Rr]eboot.*', lines[-1])
        #self.needs_restart = m is not None
        
        # PID   | PPID  | UID | User     | Command          | Service
        # ------+-------+-----+----------+------------------+-----------------
        # 1     | 0     | 0   | root     | systemd          | 
        # 409   | 1     | 0   | root     | systemd-journald | systemd-journald
        _outdated = []
        for line in lines:
            if "|" not in line:
                continue
            columns = line.split("|")
            columns = [ele.strip() for ele in columns]
            if not columns[0].isnumeric():
                continue
            
            _outdated.append({"pid": columns[0], "ppid": columns[1], "uid": columns[2], "user": columns[3], "command": columns[4], "service": columns[5]})
        
        if len(self.outdated) != len(_outdated):
            print(self.outdated)
            print(_outdated)
            raise Exception("Different outdated processes detected")
        else:
            for _process in _outdated:
                found = False
                for process in self.outdated:
                    if _process["pid"] == process["pid"]:
                        found = True
                        break
                if not found:
                    print(_outdated)
                    print(self.outdated)
                    raise Exception("Process '{}' not match in outdated processes".format(_process["pid"]))

    def getOutdatedProcesses(self):
        if self.outdated is None:
            self.__initSystemState__()
        return self.outdated
  
    def getRebootState(self):
        if self.needs_restart is None:
            self.__initSystemState__()
        return self.needs_restart
            
