import subprocess

from datetime import datetime

import re

from plugins.os.os import Os

class Repository(Os):
    DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
    HISTORY_FORMAT = "%Y-%m-%d %H:%M"
    VERSION_FORMAT = "%d.%m.%Y"
    
    '''
    >>>dnf list updates
    Last metadata expiration check: 0:01:06 ago on Sun 19 Aug 2018 04:14:00 PM IST.

    GeoIP-GeoLite-data.noarch   2018.04-1.fc26       updates                 
    GraphicsMagick.x86_64       1.3.29-1.fc26        updates                 
    ImageMagick.x86_64          6.9.9.38-1.fc26      updates                 
    '''
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
        # get repositories
        #result = subprocess.run([ "/usr/bin/dnf repolist all" ], shell=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=None )
        #lines = result.stdout.decode("utf-8").strip().split("\n")
        #repositories = []
        #for line in lines:
        #    if not line.startswith("*"):
        #        continue
        #    columns = line.split(" ")
        #    repositories.append(columns[0][1:])

        # get updates
        result = subprocess.run([ "/usr/bin/dnf -y list updates" ], shell=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=None )
        lines = result.stdout.decode("utf-8").strip().split("\n")
        lines = reversed(lines)
        updates = []
        for line in lines:
            columns = re.sub(r"\s+", " ", line).split(" ")
            
            if len(columns) < 3:# or columns[2] not in repositories:
                break
            columns = [ele.strip() for ele in columns]
            updates.append({'repository': columns[2], 'name': columns[0], 'update': columns[1] })
            #updates.append({'repository': columns[2], 'name': columns[0], 'current': None, 'update': columns[1], "arch": "" })

        return updates
      
    #def getLastUpdate(self):
    #    # get last update
    #    result = subprocess.run([ "/usr/bin/dnf history list last" ], shell=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=None )
    #    lines = result.stdout.decode("utf-8").strip().split("\n")
    #    lines = reversed(lines)
    #    current_version = ""
    #    for line in lines: 
    #        columns = line.split(" | ")
    #        
    #        date = datetime.strptime(columns[2], self.HISTORY_FORMAT)
    #        current_version = date.strftime(self.VERSION_FORMAT)
    #        break
    #    return current_version
      
    def __initSystemState__(self):
        '''
        Core libraries or services have been updated since boot-up:
          * glibc
          * linux-firmware
          * systemd

        Reboot is required to fully utilize these updates.
        More information: https://access.redhat.com/solutions/27943
        '''
        result = subprocess.run([ "/usr/bin/needs-restarting -r" ], shell=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=None )
        self.needs_restart = result.returncode == 1

        '''needs-restarting
        2438 : /usr/libexec/hald-addon-generic-backlight
        2458 : hald-addon-storage: polling /dev/sr0 (every 2 sec)
        2847 : xinetd-stayalive-pidfile/var/run/xinetd.pid
        2457 : hald-addon-acpi: listening on acpid socket /var/run/acpid.socket
        2452 : hald-addon-input: Listening on /dev/input/event7 /dev/input/event0 /dev/input/event2 /dev/input/event1
        27729 : rpc.statd'''
        #result = subprocess.run([ "/usr/bin/needs-restarting" ], shell=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=None )
        #result.stdout.decode("utf-8").strip()
        #lines = result.split("\n")
        #outdated = []
        #for line in lines:
        #    if "|" not in line:
        #        continue
        #    columns = line.split(":")
        #    columns = [ele.strip() for ele in columns]
        #    if not columns[0].isnumeric():
        #        continue
            
        #    outdated.append({"pid": columns[0], "ppid": None, "uid": None, "user": None, "command": columns[1], "service": None})
        #self.outdated = outdated
        self.outdated = []
        
    def getOutdatedProcesses(self):
        if self.outdated is None:
            self.__initSystemState__()
        return self.outdated
  
    def getRebootState(self):
        if self.needs_restart is None:
            self.__initSystemState__()
        return self.needs_restart

