import subprocess

from datetime import datetime

import re

from plugins.os.os import Os

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
        
        result = subprocess.run([ "ps", "-axo", "pid,ppid,uid,user,unit" ], shell=False, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT )
        result = result.stdout.decode("utf-8")
        lines = result.split("\n")
        processes = {}
        for line in lines:
            if not line:
               continue
            
            columns = line.split(" ")
            columns = [column for column in columns if column ]
            pid = columns.pop(0)
            processes[pid] = columns
      
        result = subprocess.run([ "/usr/bin/lsof +c0 2> /dev/null | grep \"deleted\" | grep -vP \"[0-9]+ (/tmp/|/run/|/mem)\"" ], shell=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=None )
        result = result.stdout.decode("utf-8").strip()
        lines = result.split("\n")
        outdated = []
        for line in lines:
            columns = re.sub(r"\s+", " ", line).split(" ")
            
            pid = columns[1]
            if pid in processes:
                process_details = processes[pid]
                ppid, uid, user, unit = process_details
                if unit == "-":
                    unit = ""
                else:
                    unit = unit.rsplit(".",1)
                    if len(unit) == 1 or unit[1] != "service":
                        unit = ""
                    else:
                        unit = unit[0]
            else:
                ppid = ""
                uid = ""
                user = ""
                unit = ""
                
            outdated.append({"pid": columns[1], "ppid": ppid, "uid": uid, "user": user, "command": columns[0], "service": unit})
        self.outdated = outdated
        
    def getOutdatedProcesses(self):
        if self.outdated is None:
            self.__initSystemState__()
        return self.outdated
  
    def getRebootState(self):
        if self.needs_restart is None:
            self.__initSystemState__()
        return self.needs_restart

