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
        result = subprocess.run([ "/usr/bin/needrestart -r i" ], shell=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=None )
        result.stdout.decode("utf-8").strip().split("\n")
        self.needs_restart = False
        self.outdated = []

    def getLastUpdate(self):
        # get last update
        result = subprocess.run([ "/usr/bin/dnf history list last" ], shell=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=None )
        lines = result.stdout.decode("utf-8").strip().split("\n")
        lines = reversed(lines)
        self.current_version = ""
        for line in lines: 
            columns = line.split(" | ")
            
            date = datetime.strptime(columns[2], self.HISTORY_FORMAT)
            self.current_version = date.strftime(self.VERSION_FORMAT)
            break

        return self.current_version

    def getUpdates(self, last_updates):
        # get repositories
        result = subprocess.run([ "/usr/bin/dnf repolist all" ], shell=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=None )
        lines = result.stdout.decode("utf-8").strip().split("\n")
        repositories = []
        for line in lines:
            if not line.startswith("*"):
                continue
            columns = line.split(" ")
            repositories.append(columns[0][1:])

        # get updates
        result = subprocess.run([ "/usr/bin/dnf -y list updates" ], shell=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=None )
        lines = result.stdout.decode("utf-8").strip().split("\n")
        lines = reversed(lines)
        self.updates = []
        for line in lines:
            columns = re.sub(r"\s+", " ", line).split(" ")
            
            if len(columns) < 3 or columns[2] not in repositories:
                break
            columns = [ele.strip() for ele in columns]
            self.updates.append({'repository': columns[2], 'name': columns[0], 'current': None, 'update': columns[1], "arch": "" })

        return self.updates
      
    def getRebootState(self):
        return self.needs_restart

    def getOutdatedProcesses(self):
        return self.outdated

