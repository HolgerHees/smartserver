import subprocess
import re

import timeit

class Processlist():
    @staticmethod
    def getProcessIds():
        result = subprocess.run([ "/usr/bin/ps", "-axo", "pid" ], shell=False, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT )
        lines = result.stdout.decode("utf-8").split("\n")
        pids = [line.strip() for line in lines]
        return pids
        
    @staticmethod
    def getProcesslist():
        result = subprocess.run([ "/usr/bin/ps", "-axo", "pid,ppid,uid,user,comm,unit" ], shell=False, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT )
        lines = result.stdout.decode("utf-8").split("\n")
        processes = {}
        for line in lines:
            if not line:
               continue
            
            columns = line.split(" ")
            columns = [column for column in columns if column ]
            if columns[5] == "-":
                columns[5] = ""
            pid = columns.pop(0)
            processes[pid] = columns
        return processes

    @staticmethod
    def getOutdatedProcessIds():
        #result = subprocess.run([ "/usr/bin/lsof -n +c0 2> /dev/null | grep \"deleted\" | grep -vP \"[0-9]+ (/tmp/|/run/|/mem|/proc)\"" ], shell=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=None )
        #result = subprocess.run([ "/usr/bin/lsof", "-n", "+c0", "+aL1", "/" ], shell=False, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=None )
        
        result = subprocess.run([ "/usr/bin/lsof", "-t", "-n", "+aL1", "/" ], shell=False, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=None )
        outdated_pids = result.stdout.decode("utf-8").strip().split("\n")
        
        processes = Processlist.getProcesslist()
        
        outdated = []
        if outdated_pids[0]:
            for pid in outdated_pids:
                if pid not in processes:
                    continue
                  
                process_details = processes[pid]
                ppid, uid, user, comm, unit = process_details
                _unit = unit.rsplit(".",1)
                if len(_unit) == 1 or _unit[1] != "service":
                    unit = ""
                else:
                    unit = _unit[0]
                          
                outdated.append({"pid": pid, "ppid": ppid, "uid": uid, "user": user, "command": comm, "service": unit})
            
        return outdated
