import subprocess
import re

import sys
import os
import glob

import timeit


class Processlist():
    # credits goes to https://raw.githubusercontent.com/rpm-software-management/yum-utils/master/needs-restarting.py
    @staticmethod
    def _getService(pid):
        fname = '/proc/%s/cgroup' % pid
        try:
            with open(fname, 'r') as f:
                groups = f.readlines()
        except (IOError, OSError) as e:
            return None

        for line in groups:
            line = line.replace('\n', '')
            hid, hsub, cgroup = line.split(':')
            if hsub == 'name=systemd':
                name = cgroup.split('/')[-1]
                if name.endswith('.service'):
                    return name
        return None

    @staticmethod
    def _getOpenFiles(pid):
        files = []
        smaps = '/proc/%s/smaps' % pid
        try:
            with open(smaps, 'r') as maps_f:
                maps = maps_f.readlines()
        except (IOError, OSError) as e:
            return files

        for line in maps:
            slash = line.find('/')
            if slash == -1 or line.find('00:') != -1: # if we don't have a '/' or if we fine 00: in the file then it's not _REALLY_ a file
                continue
            line = line.replace('\n', '')
            filename = line[slash:]
            filename = filename.split(';')[0]
            filename = filename.strip()
            if filename not in files:
                files.append(filename)
        return files

    @staticmethod
    def getProcessIds():
        pids = []
        for fn in glob.glob('/proc/[0123456789]*'):
            pids.append(os.path.basename(fn))
        return pids

    #@staticmethod
    #def getProcessIds():
    #    result = subprocess.run([ "/usr/bin/ps", "-axo", "pid" ], shell=False, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT )
    #    lines = result.stdout.decode("utf-8").split("\n")
    #    pids = [line.strip() for line in lines]
    #    return pids
        
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
        
        #result = subprocess.run([ "/usr/bin/lsof", "-t", "-n", "+aL1", "/" ], shell=False, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=None )
        #outdated_pids = result.stdout.decode("utf-8").strip().split("\n")
        
        outdated_pids = set()
        for pid in Processlist.getProcessIds():
            for fn in Processlist._getOpenFiles(pid):
                # if the file is deleted 
                if fn.find('(deleted)') != -1: 
                    outdated_pids.add(pid)
                    break
                  
        processes = Processlist.getProcesslist()
        
        outdated = []
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
