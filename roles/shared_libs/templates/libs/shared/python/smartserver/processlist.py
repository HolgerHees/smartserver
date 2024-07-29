import subprocess
import re
import time
import logging

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
    def _getCmdline(pid):
        fname = '/proc/%s/cmdline' % pid
        try:
            with open(fname, 'rb') as f:
                return f.read().replace(b'\0', b' ').decode().strip()
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
        try:
            with open('/proc/%s/smaps' % pid, 'r') as f:
                smaps = f.readlines()
        except (IOError, OSError) as e:
            return files

        # inspired by https://github.com/stdevel/yum-plugin-needs-restarting/blob/master/needs-restarting.py
        for line in smaps:
            slash = line.find('/')
            if slash == -1 or line.find(' 00:') != -1: # if we don't have a '/' or if we fine 00: in the file then it's not _REALLY_ a file
                continue
            line = line.replace('\n', '')
            filename = line[slash:]
            filename = filename.split(';')[0]
            filename = filename.strip()
            if filename[-9:] != "(deleted)":
                continue
            filename = filename[:-10]
            files.append(filename)
        return set(files)

    @staticmethod
    def getPids(pattern=None,ppid=None):
        if pattern is not None or ppid is not None:
            cmd = [ "/usr/bin/pgrep" ]
            if ppid is None:
                cmd.append("-f")
            else:
                cmd.append("-fP")
                cmd.append(str(ppid))

            if pattern is not None:
                cmd.append(pattern)

            result = subprocess.run(cmd, shell=False, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT )
            if result.returncode == 0:
                return result.stdout.decode().strip().split("\n")
            else:
                return []
        else:
            pids = []
            with os.scandir("/proc/") as it:
                for entry in it:
                    if not entry.is_dir() or not entry.name.isnumeric():
                        continue
                    pids.append(entry.name)
            #for fn in glob.glob('/proc/[0123456789]*'):
            #    pids.append(os.path.basename(fn))
            return pids

    @staticmethod
    def checkPid(pid):
        return os.path.exists('/proc/%s' % pid)

    @staticmethod
    def getCmdLine(pid):
        return Processlist._getCmdline(pid)
        
    @staticmethod
    def getOutdatedProcessIds():
        #start = time.time()
        outdated_pids = set()
        for pid in Processlist.getPids():
            for fn in Processlist._getOpenFiles(pid):
                if re.search('^(?!.*/(tmp|var|run)).*$', fn):
                    outdated_pids.add(pid)
                    break

        #logging.info(outdated_pids)
        #end = time.time()
        #logging.info(end-start)

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
