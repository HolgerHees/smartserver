from config import config

from server.watcher import watcher


class SoftwareVersionWatcher(watcher.Watcher): 
    def __init__(self, handler):
        super().__init__()

        self.handler = handler

        self.software = {}
        self.update_count = 0

        self.initSoftwareState(False)
        
    def notifyChange(self, event):
        self.initSoftwareState(True)
        self.handler.notifyWatcherSoftwareVersions( "software", self.software)
        self.handler.notifyWatcherSoftwareVersions( "update_count", self.update_count)

    def initSoftwareState(self, shouldRetry):
        software = self.readJsonFile(config.software_version_state_file,shouldRetry,{})
        update_count = 0
        if "states" in software:
            for state in software["states"]:
                if len(state["updates"]) > 0:
                    update_count += 1
        self.software = software
        self.update_count = update_count

    def getSoftwareVersions(self):
        return self.software

    def getVersionCount(self):
        return self.update_count
