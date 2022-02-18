import subprocess
import re

import sys
import os
import glob

import timeit
import json

class Processlist():
    # credits goes to https://raw.githubusercontent.com/rpm-software-management/yum-utils/master/needs-restarting.py
    @staticmethod
    def _getUserMap():
        user_map = {}
        fname = '/etc/passwd'
        try:
            with open(fname, 'r') as f:
                lines = f.readlines()
        except (IOError, OSError) as e:
            return files

        for line in lines:
            columns = line.split(":",3)
            user_map[columns[2]] = columns[0]

        return user_map

    @staticmethod
    def _getGroupMap():
        group_map = {}
        fname = '/etc/group'
        try:
            with open(fname, 'r') as f:
                lines = f.readlines()
        except (IOError, OSError) as e:
            return files

        for line in lines:
            columns = line.split(":",3)
            group_map[columns[2]] = columns[0]

        return group_map

    @staticmethod
    def _getPPID(pid):
        fname = '/proc/%s/stat' % pid
        try:
            with open(fname, 'r') as f:
                return f.read().split(" ")[3]
        except (IOError, OSError) as e:
            return None

    @staticmethod
    def _getUID(pid):
        fname = '/proc/%s' % pid
        try:
            stat_info = os.stat(fname)
            uid = stat_info.st_uid
            return str(uid)
        except Exception as e:
            return None

    @staticmethod
    def _getComm(pid):
        fname = '/proc/%s/comm' % pid
        try:
            with open(fname, 'r') as f:
                return f.read().strip()
        except (IOError, OSError) as e:
            return None

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
            if cgroup.startswith("/system.slice/"):
                name = cgroup[14:]
                if name.endswith('.service'):
                    return name[:-8]
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
        
    #@staticmethod
    #def getProcesslist():
    #    result = subprocess.run([ "/usr/bin/ps", "-axo", "pid,ppid,uid,user,comm,unit" ], shell=False, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT )
    #    lines = result.stdout.decode("utf-8").split("\n")
    #    processes = {}
    #    for line in lines:
    #        if not line:
    #           continue
            
    #        columns = line.split(" ")
    #        columns = [column for column in columns if column ]
    #        if columns[5] == "-":
    #            columns[5] = ""
    #        pid = columns.pop(0)
    #        processes[pid] = columns
    #    return processes

    @staticmethod
    def getOutdatedProcessIds():
        #result = subprocess.run([ "/usr/bin/lsof -n +c0 2> /dev/null | grep \"deleted\" | grep -vP \"[0-9]+ (/tmp/|/run/|/mem|/proc)\"" ], shell=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=None )
        #result = subprocess.run([ "/usr/bin/lsof", "-n", "+c0", "+aL1", "/" ], shell=False, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=None )
        
        #result = subprocess.run([ "/usr/bin/lsof", "-t", "-n", "+aL1", "/" ], shell=False, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=None )
        #outdated_pids = result.stdout.decode("utf-8").strip().split("\n")
        
        
        #result = subprocess.run([ "/usr/bin/systemctl", "list-unit-files", "--state=enabled,disabled", "--no-pager", "--output=json" ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        #if result.returncode != 0:
        #    raise Exception(result.stdout.decode("utf-8"))
        #json_data = json.loads(result.stdout.decode("utf-8"))
        #valid_services = []
        #for service in json_data:
        #    if service['unit_file'].endswith('.service'):
        #         valid_services.append(service['unit_file'][:-8])

        outdated_pids = set()
        for pid in Processlist.getProcessIds():
            for fn in Processlist._getOpenFiles(pid):
                # if the file is deleted 
                if re.search('^(?!.*/tmp/|/var/|/run/).*\(deleted\)$', fn):
                #if fn.find('(deleted)') != -1:
                    outdated_pids.add(pid)
                    break
                  
        outdated = {}
        if len(outdated_pids) > 0:
            user_map = Processlist._getUserMap()
            for pid in outdated_pids:
                ppid = Processlist._getPPID(pid)
                if ppid is None:
                    continue

                uid = Processlist._getUID(pid)
                if uid is None:
                    continue
                user = user_map[uid] if uid in user_map else uid

                comm = Processlist._getComm(pid)
                if comm is None:
                    continue
                
                unit = Processlist._getService(pid)
                if unit is None:
                    unit = ""
                else:
                    result = subprocess.run([ "/usr/bin/systemctl", "show", unit, "--no-page" ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                    if result.returncode != 0:
                        raise Exception(result.stdout.decode("utf-8"))
                    if not re.search("UnitFileState=(enabled|disabled)", result.stdout.decode("utf-8")):
                        unit = ""

                outdated[pid] = {"pid": pid, "ppid": ppid, "uid": uid, "user": user, "command": comm, "service": unit}
            
        return outdated
