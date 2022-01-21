import subprocess
import re

from datetime import datetime

from plugins.os.os import Os

class Repository(Os):
    DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
    HISTORY_FORMAT = "%Y-%m-%d %H:%M:%S"
    VERSION_FORMAT = "%d.%m.%Y"
  
    def __init__(self):                      
        result = subprocess.run([ "/usr/bin/zypper ps -s" ], shell=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=None )
        result = result.stdout.decode("utf-8").strip()
        
        # Ein Neustart wird benötigt, um sicher zu stellen, dass ihr System von diesen Updates profitiert.
        m = re.search('[Nn]eustart|restart|reboot', result)
        self.needs_restart = m.group(0) is not None
        
        # PID   | PPID  | UID | User     | Command          | Service
        # ------+-------+-----+----------+------------------+-----------------
        # 1     | 0     | 0   | root     | systemd          | 
        # 409   | 1     | 0   | root     | systemd-journald | systemd-journald
        outdated = []
        lines = result.split("\n")
        for line in lines:
            if "|" not in line:
                continue
            columns = line.split("|")
            columns = [ele.strip() for ele in columns]
            if not columns[0].isnumeric():
                continue
            
            outdated.append({"pid": columns[0], "ppid": columns[1], "uid": columns[2], "user": columns[3], "command": columns[4], "service": columns[5]})
        self.outdated = outdated

    def getLastUpdate(self):
        # get last update
        self.current_version = ""
        with open("/var/log/zypp/history") as f:
            lines = f.readlines()
            lines = reversed(lines)
            for line in lines:
                if line.startswith("#"):
                    continue;

                columns = line.split("|")
                date = datetime.strptime(columns[0], self.HISTORY_FORMAT)
                self.current_version = date.strftime(self.VERSION_FORMAT)
                break

        return self.current_version

    def getUpdates(self):
        # get updates
        result = subprocess.run([ "/usr/bin/zypper list-updates" ], shell=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=None )
        lines = result.stdout.decode("utf-8").strip().split("\n")
        lines = reversed(lines)
        self.updates = []
        for line in lines:
            columns = line.split(" | ")
            if len(columns) < 5:
                break
            columns = [ele.strip() for ele in columns]
            self.updates.append({'repository': columns[1], 'name': columns[2], 'current': columns[3], 'update': columns[4], 'arch': columns[5] })

        return self.updates
      
    def getOutdatedProcesses(self):
        return self.outdated
  
    def getRebootState(self):
        return self.needs_restart
      
