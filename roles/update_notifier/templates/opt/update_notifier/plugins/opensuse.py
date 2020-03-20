import subprocess

from helper.version import Version

from datetime import datetime

from plugins.plugin import Plugin

class Repository(Plugin):
    DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
    HISTORY_FORMAT = "%Y-%m-%d %H:%M:%S"
    VERSION_FORMAT = "%d.%m.%Y"
  
    '''
    >>>zypper lu
    Repository-Daten werden geladen...
    Installierte Pakete werden gelesen...
    S | Repository             | Name   | Aktuelle Version  | Verfügbare Version | Arch  
    --+------------------------+--------+-------------------+--------------------+-------
    v | Main Update Repository | dracut | 044.2-lp151.2.9.1 | 044.2-lp151.2.12.1 | x86_64
    v | Main Update Repository | pam    | 1.3.0-lp151.8.3.1 | 1.3.0-lp151.8.6.1  | x86_64

    >>>zypper lu
    Repository-Daten werden geladen...
    Installierte Pakete werden gelesen...
    Keine Aktualisierungen gefunden.
    '''
    def __init__(self,plugin_config,global_config):
        # get updates
        result = subprocess.run([ "/usr/bin/zypper list-updates" ], shell=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=None )
        lines = result.stdout.decode("utf-8").strip().split("\n")
        lines = reversed(lines)
        self.updates = []
        for line in lines:
            columns = line.split(" | ")
            if len(columns) < 5:
                break
              
            self.updates.append({'repository': columns[1], 'name': columns[2], 'current': columns[3], 'update': columns[4] })
        
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
