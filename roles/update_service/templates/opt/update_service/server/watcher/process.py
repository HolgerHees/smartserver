import threading
from datetime import datetime, timedelta
import re
import logging
import time

from smartserver.processlist import Processlist

from server.watcher import watcher

class ProcessWatcher(watcher.Watcher): 
    def __init__(self, operating_system ):
        super().__init__()
        
        self.reboot_required_services = []
        for string_pattern in operating_system.getRebootRequiredServices():
            regex_pattern = re.compile(string_pattern)
            self.reboot_required_services.append(regex_pattern)
            
        self.operating_system = operating_system
        
        self.is_running = True
        self.last_refresh = self.last_cleanup = datetime.now() - timedelta(hours=24) # to force a full refresh

        self.prioritized_state_refresh_after_reboot = ( datetime.now() + timedelta(minutes=5) ) if time.monotonic() < 300 else None
        
        self.is_reboot_needed_by_core_update = False
        self.system_reboot_modified = self.getStartupTimestamp()
        
        self.is_reboot_needed_by_outdated_processes = False
        self.is_update_service_outdated = False
        self.outdated_services = []
        self.outdated_processes = {}
        self.oudated_processes_modified = self.getStartupTimestamp()
        
        self.event = threading.Event()
        self.lock = threading.Lock()

        self.thread = threading.Thread(target=self.checkProcesses, args=())
        self.thread.start()

    def process(self, outdated_processes):
        is_reboot_needed = False
        for pid in outdated_processes:
            service = outdated_processes[pid]["service"]
            if service == "":
                is_reboot_needed = True
                break
            else:
                for regex_pattern in self.reboot_required_services:
                    if regex_pattern.match(service):
                        is_reboot_needed = True
                        break
                     
        is_update_service_outdated = False
        services = []
        for pid in outdated_processes:
            service = outdated_processes[pid]["service"]
            if not service:
                continue
            if service == "update_service":
                is_update_service_outdated = True
            services.append(service)
        self.outdated_services = list(set(services))
        
        self.outdated_processes = outdated_processes
        
        self.is_update_service_outdated = is_update_service_outdated
        self.is_reboot_needed_by_outdated_processes = is_reboot_needed
        self.oudated_processes_modified = self.getNowAsTimestamp()

    def checkProcesses(self):  
        while self.is_running:
            timeout = 900

            if ( datetime.now() - self.last_refresh ).total_seconds() >= 900:
                self._refresh()
            elif ( datetime.now() - self.last_cleanup ).total_seconds() >= 15:
                self._cleanupRebootState()
                self._cleanupPIDs()

            if self._cleanupRequired():
                timeout = 15

            self.event.wait(timeout)
            self.event.clear()
        
    def terminate(self):
        self.is_running = False
        self.event.set()
        
    def refresh(self):
        self._refresh()
        self.event.set()

    def cleanup(self):
        self._cleanupRebootState()
        self._cleanupPIDs()
        self.event.set()

    def _refresh(self):
        with self.lock:
            logging.info("Refresh outdated processlist & reboot state")

            self._refreshRebootState()

            outdated_processes = Processlist.getOutdatedProcessIds()
            if outdated_processes.keys() != self.outdated_processes.keys():
                logging.info("new outdated processe(s)")
                self.process(outdated_processes)

            self.last_refresh = self.last_cleanup = datetime.now()

    def _cleanupRequired(self):
        return self.prioritized_state_refresh_after_reboot is not None or len(self.outdated_processes) > 0

    def _cleanupRebootState(self):
        if self.prioritized_state_refresh_after_reboot is None:
            return

        if self.is_reboot_needed_by_core_update:
            if datetime.now() < self.prioritized_state_refresh_after_reboot:
                with self.lock:
                    self._refreshRebootState()

    def _cleanupPIDs(self):
        if len(self.outdated_processes) == 0:
            return

        with self.lock:
            processIds = Processlist.getPids()
            outdated_processes = {k: v for k, v in self.outdated_processes.items() if k in processIds}

            if len(self.outdated_processes) != len(outdated_processes):
                logging.info("{} outdated processe(s) cleaned".format( len(self.outdated_processes) - len(outdated_processes) ))
                self.process(outdated_processes)

                self.last_cleanup = datetime.now()

    def _refreshRebootState(self):
        is_reboot_needed_by_core_update = self.operating_system.getRebootState()
        if self.is_reboot_needed_by_core_update != is_reboot_needed_by_core_update:
            logging.info("Reboot state changed to '{}'".format( 'needed' if is_reboot_needed_by_core_update else 'not needed'))
            self.is_reboot_needed_by_core_update = is_reboot_needed_by_core_update
            self.system_reboot_modified = self.getNowAsTimestamp()

        if not self.is_reboot_needed_by_core_update:
            self.prioritized_state_refresh_after_reboot = None

    def getOudatedProcesses(self):
        return list(self.outdated_processes.values())
      
    def getOutdatedServices(self):
        return self.outdated_services
      
    def isUpdateServiceOutdated(self):
        return self.is_update_service_outdated

    def isRebootNeededByCoreUpdate(self):
        if self.prioritized_state_refresh_after_reboot is not None:
            return False

        return self.is_reboot_needed_by_core_update

    def isRebootNeededByOutdatedProcesses(self):
        return self.is_reboot_needed_by_outdated_processes
      
    def getOutdatedProcessesLastModifiedAsTimestamp(self):
        return self.oudated_processes_modified

    def getSystemRebootLastModifiedAsTimestamp(self):
        return self.system_reboot_modified

    def getLastRefreshAsTimestamp(self):
        return round(self.last_refresh.timestamp(),3)
