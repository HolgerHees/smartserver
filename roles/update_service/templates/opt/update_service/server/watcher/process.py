import threading
import re
import logging
import time

from smartserver.processlist import Processlist
from smartserver.metric import Metric

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
        "systemctl restart": "service_restart",
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
        self.last_refresh = self.last_cleanup = 0 # to force a full refresh

        self.forced_reboot_state_refresh_after_reboot = time.time() + 300 if time.monotonic() < 300 else None
        
        self.is_reboot_needed_by_core_update = False
        
        self.is_reboot_needed_by_outdated_processes = False
        self.is_update_service_outdated = False
        self.outdated_services = []
        self.outdated_processes = {}
        
        self.external_cmd_pids = {}
        self.current_pids = []

        self.event = threading.Event()
        self.lock = threading.Lock()

        self.thread = threading.Thread(target=self._checkProcesses, args=())

    def start(self):
        self.thread.start()

    def terminate(self):
        self.is_running = False
        self.event.set()
        self.thread.join()

    def _checkProcesses(self):
        logging.info("ProcessWatcher started")

        try:
            force_refresh = False
            while self.is_running:
                if force_refresh or ( time.time() - self.last_refresh ) >= 900:
                    self.refresh()
                else:
                    self.cleanup()

                timeout = 15 if self.forced_reboot_state_refresh_after_reboot is not None or len(self.outdated_processes) > 0 else 900
                self.event.wait(timeout)

                force_refresh = self.event.is_set()
                self.event.clear()
        except Exception as e:
            self.is_running = False
            raise e
        finally:
            logging.info("ProcessWatcher stopped")

    def refresh(self):
        with self.lock:
            logging.info("Refresh outdated processlist & reboot state")

            self._refreshRebootState()

            outdated_processes = Processlist.getOutdatedProcessIds()
            if outdated_processes.keys() != self.outdated_processes.keys():
                logging.info("new outdated processe(s)")
                self._processOutdatedProcesses(outdated_processes)

            self.last_refresh = self.last_cleanup = time.time()

    def cleanup(self):
        if self.forced_reboot_state_refresh_after_reboot is not None:
            if self.is_reboot_needed_by_core_update:
                if time.time() < self.forced_reboot_state_refresh_after_reboot:
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

        self.last_cleanup = time.time()

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

        self.handler.notifyWatcherProcessState()

    def _refreshRebootState(self):
        is_reboot_needed_by_core_update = self.operating_system.getRebootState()
        if self.is_reboot_needed_by_core_update != is_reboot_needed_by_core_update:
            logging.info("Reboot state changed to '{}'".format( 'needed' if is_reboot_needed_by_core_update else 'not needed'))
            self.is_reboot_needed_by_core_update = is_reboot_needed_by_core_update

        if not self.is_reboot_needed_by_core_update:
            self.forced_reboot_state_refresh_after_reboot = None

    def refreshExternalCmdType(self, daemon_job_is_running):
        cleaned = False

        if not daemon_job_is_running:
            # 10 times faster then Processlist.getPids(" |".join( ProcessWatcher.process_mapping.keys()))
            current_pids = Processlist.getPids()
            if current_pids is not None:
                current_pids.sort()

                if current_pids != self.current_pids:
                    for pid in set(current_pids) - set(self.current_pids):
                        cmdline = Processlist.getCmdLine(pid)
                        if not cmdline:
                            continue
                        for term in ProcessWatcher.process_mapping:
                            if "{} ".format(term) in cmdline and not self.operating_system.isRunning(cmdline):
                                self.external_cmd_pids[pid] = ProcessWatcher.process_mapping[term]
                        #logging.info("check {} {}".format(pid,cmdline))

                    for pid in set(self.current_pids) - set(current_pids):
                        if pid in self.external_cmd_pids:
                            del self.external_cmd_pids[pid]
                            cleaned = True

                self.current_pids = current_pids
        else:
            self.current_pids = []

        if cleaned and len(self.external_cmd_pids) == 0:
            self.event.set()

        #logging.info("DEBUG: Process.refreshExternalCmdType: " + str(daemon_job_is_running) + " " + str(self.external_cmd_pids))
        #logging.info("DEBUG: Process.refreshExternalCmdType: " + str(daemon_job_is_running) + " " + str(self.current_pids))

        return None if len(self.external_cmd_pids) == 0 else next(iter(self.external_cmd_pids.values()))

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
      
    def getLastRefreshAsTimestamp(self):
        return round(self.last_refresh,3)

    def getStateMetrics(self):
        return [
            Metric.buildProcessMetric("update_service", "process_watcher", "1" if self.is_running else "0")
        ]
