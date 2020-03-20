import subprocess

from helper.version import Version

from datetime import datetime

from plugins.plugin import Plugin

import re

class Repository(Plugin):
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
    def __init__(self,plugin_config,global_config):
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
            
            self.updates.append({'repository': columns[2], 'name': columns[0], 'current': None, 'update': columns[1] })
                      
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

    def getCurrentVersion(self):
        return self.createUpdate( version = self.current_version, branch = 'master', date = self.current_version, url = None )

    def getCurrentVersionString(self):
        return self.current_version

    def getUpdates(self, last_updates):
        current_update = last_updates[0] if last_updates is not None and len(last_updates) > 0 else None

        new_updates_r = {}
        if len(self.updates) > 0:
            version = "{} updates".format(len(self.updates))
            
            if current_update != None and current_update['version'] == version:
                new_updates_r['master'] = current_update
            else:
                date_str = datetime.now().strftime(self.DATETIME_FORMAT)
                new_updates_r['master'] = self.createUpdate( version = version, branch = 'master', date = date_str, url = None )
            
        return new_updates_r
