import threading
from datetime import datetime, timedelta
import re
import logging
import time

from smartserver.processlist import Processlist

from server.watcher import watcher

class ProcessWatcher(watcher.Watcher): 
    process_mapping = {
        "software_update_check": "software_check",
        "system_update_check": "update_check",
        "ansible-playbook": "deployment_update",
        "rpm": "system_update",
        "yum": "system_update",
        "apt": "system_update",
        "dnf": "system_update",
        "zypper": "system_update",
        "systemctl": "service_restart",
    }

    def __init__(self, handler, operating_system ):
        super().__init__()

        self.handler = handler

        self.reboot_required_services = []
        for string_pattern in operating_system.getRebootRequiredServices():
            regex_pattern = re.compile(string_pattern)
            self.reboot_required_services.append(regex_pattern)

        self.operating_system = operating_system

        self.is_running = True
        self.last_refresh = self.last_cleanup = datetime.now() - timedelta(hours=24) # to force a full refresh

        self.forced_reboot_state_refresh_after_reboot = ( datetime.now() + timedelta(minutes=5) ) if time.monotonic() < 300 else None
        
        self.is_reboot_needed_by_core_update = False
        self.system_reboot_modified = self.getStartupTimestamp()
        
        self.is_reboot_needed_by_outdated_processes = False
        self.is_update_service_outdated = False
        self.outdated_services = []
        self.outdated_processes = {}
        self.oudated_processes_modified = self.getStartupTimestamp()
        
        self.external_cmd_type = None
        self.external_cmd_type_pid = None
        self.current_pids = []

        self.event = threading.Event()
        self.lock = threading.Lock()

        self.thread = threading.Thread(target=self._checkProcesses, args=())
        self.thread.start()

    def _checkProcesses(self):
        while self.is_running:
            timeout = 900

            if ( datetime.now() - self.last_refresh ).total_seconds() >= 900:
                self.refresh()
            else:
                self.cleanup()

            if self.forced_reboot_state_refresh_after_reboot is not None or len(self.outdated_processes) > 0:
                timeout = 15

            self.event.wait(timeout)
            self.event.clear()
        
    def terminate(self):
        self.is_running = False
        self.event.set()

    def refresh(self):
        with self.lock:
            logging.info("Refresh outdated processlist & reboot state")

            self._refreshRebootState()

            outdated_processes = Processlist.getOutdatedProcessIds()
            if outdated_processes.keys() != self.outdated_processes.keys():
                logging.info("new outdated processe(s)")
                self._processOutdatedProcesses(outdated_processes)

            self.last_refresh = datetime.now()

    def cleanup(self):
        if self.forced_reboot_state_refresh_after_reboot is not None:
            if self.is_reboot_needed_by_core_update:
                if datetime.now() < self.forced_reboot_state_refresh_after_reboot:
                    with self.lock:
                        self._refreshRebootState()
                else:
                    self.forced_reboot_state_refresh_after_reboot = None

        if len(self.outdated_processes) > 0:
            with self.lock:
                processIds = Processlist.getPids()
                outdated_processes = {k: v for k, v in self.outdated_processes.items() if k in processIds}
                if len(self.outdated_processes) != len(outdated_processes):
                    logging.info("{} outdated processe(s) cleaned".format( len(self.outdated_processes) - len(outdated_processes) ))
                    self._processOutdatedProcesses(outdated_processes)

    def _processOutdatedProcesses(self, outdated_processes):
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

        self.handler.notifyWatcherProcessState()

    def _refreshRebootState(self):
        is_reboot_needed_by_core_update = self.operating_system.getRebootState()
        if self.is_reboot_needed_by_core_update != is_reboot_needed_by_core_update:
            logging.info("Reboot state changed to '{}'".format( 'needed' if is_reboot_needed_by_core_update else 'not needed'))
            self.is_reboot_needed_by_core_update = is_reboot_needed_by_core_update
            self.system_reboot_modified = self.getNowAsTimestamp()

        if not self.is_reboot_needed_by_core_update:
            self.forced_reboot_state_refresh_after_reboot = None

    def refreshExternalCmdType(self, daemon_job_is_running):
        if not daemon_job_is_running:
            if self.external_cmd_type_pid is None or not Processlist.checkPid(self.external_cmd_type_pid):

                external_cmd_type = None
                external_cmd_type_pid = None

                # 10 times faster then Processlist.getPids(" |".join( ProcessWatcher.process_mapping.keys()))
                current_pids = Processlist.getPids()
                if current_pids is not None and current_pids != self.current_pids:
                    for pid in set(current_pids) - set(self.current_pids):
                        cmdline = Processlist.getCmdLine(pid)
                        if not cmdline:
                            continue
                        for term in ProcessWatcher.process_mapping:
                            if "{} ".format(term) in cmdline and not self.operating_system.isRunning(cmdline):
                                external_cmd_type_pid = pid
                                external_cmd_type = ProcessWatcher.process_mapping[term]
                                break
                        if external_cmd_type is not None:
                            break
                        #logging.info("check {} {}".format(pid,cmdline))
                    self.current_pids = current_pids

                #pids = Processlist.getPids(" |".join( ProcessWatcher.process_mapping.keys()))
                #if pids is not None:
                #    for pid in pids:
                #        cmdline = Processlist.getCmdLine(pid)
                #        if cmdline is not None:
                #            for term in ProcessWatcher.process_mapping:
                #                if "{} ".format(term) in cmdline:
                #                    external_cmd_type_pid = pid
                #                    external_cmd_type = ProcessWatcher.process_mapping[term]
                #                    break
                #            if external_cmd_type is not None:
                #                break
            else:
                self.current_pids = []
                external_cmd_type = self.external_cmd_type
                external_cmd_type_pid = self.external_cmd_type_pid
        else:
            self.current_pids = []
            external_cmd_type = None
            external_cmd_type_pid = None

        if self.external_cmd_type != external_cmd_type:
            self.external_cmd_type = external_cmd_type
            self.external_cmd_type_pid = external_cmd_type_pid

            self.last_refresh = datetime.now() - timedelta(hours=24)
            self.event.set()

        return self.external_cmd_type

    def getOutdatedProcesses(self):
        return list(self.outdated_processes.values())
      
    def getOutdatedServices(self):
        return self.outdated_services
      
    def isUpdateServiceOutdated(self):
        return self.is_update_service_outdated

    def isRebootNeededByCoreUpdate(self):
        if self.forced_reboot_state_refresh_after_reboot is not None:
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
