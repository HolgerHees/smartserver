import sys
import os
import subprocess
import traceback
import glob
import threading
import logging

import time

import pexpect 
from pexpect.exceptions import EOF, TIMEOUT

from datetime import datetime, timedelta

from config import config

from smartserver.logfile import LogFile
from smartserver import command
from smartserver import processlist

from server.watcher import watcher


class CmdExecuter(watcher.Watcher): 
    START_TIME_STR_FORMAT = "%Y.%m.%d_%H.%M.%S"

    env_path = "/sbin:/usr/sbin:/usr/local/sbin:/usr/local/bin:/usr/bin:/bin"
    home_path = "/root"

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

    def __init__(self, handler, process_watcher, operating_system):
        super().__init__()
      
        self.handler = handler
        self.process_watcher = process_watcher
        self.operating_system = operating_system

        self.killed_job = False
        self.killed_logfile = None
        
        self.current_cmd_type = None
        self.current_started = None
        self.current_logfile = None
        self.current_child = None
        
        self.last_jobs_modified = 0
        self.jobs = []
        self.initJobs()
        
        self.external_cmd_type = None
        self.external_cmd_type_pid = None

        self.current_pids = []

        self.is_running = True
        self.event = threading.Event()
        self.thread = threading.Thread(target=self._checkExternalCmdTypes, args=())
        self.thread.start()

    def terminate(self):
        self.is_running = False
        self.event.set()
            
    def isInterruptableJob(self,cmd_type):
        return cmd_type in [ "system_reboot", "daemon_restart" ]
    
    def initJobs(self):
        _jobs = []
        _last_jobs_modified = 0
        
        files = glob.glob(u"{}*.log".format(config.job_log_folder))
        files.sort(key=os.path.getmtime, reverse=True)
        for name in files:
            filename = os.path.basename(name)
            data = filename.split("-")
            
            job = {}
            job["timestamp"] = datetime.strptime(data[0],"%Y.%m.%d_%H.%M.%S").timestamp();
            job["start"] = data[0];
            job["duration"] = data[1];
            job["state"] = data[2];
            job["type"] = data[3];
            job["user"] = data[4].split(".")[0]
            
            job_timestamp = round(os.path.getmtime(name),3)
            if job_timestamp > _last_jobs_modified:
                _last_jobs_modified = job_timestamp
            
            _jobs.append(job)
            
        self.jobs = _jobs;
        self.last_jobs_modified = _last_jobs_modified

    def getJobs(self):
        return self.jobs
        
    def getLastJobsModifiedAsTimestamp(self):
        return self.last_jobs_modified
      
    def getCurrentJobStarted(self):
        return self.current_started
      
    def getCurrentJobLogfile(self):
        return self.current_logfile
      
    def getCurrentJobCmdType(self):
        return self.current_cmd_type
      
    def isRunning(self):
        return self.isDaemonJobRunning() or self.getExternalCmdType() != None
      
    def isDaemonJobRunning(self):
        return self.current_started != None
      
    def isExternalJobRunning(self):
        return self.getExternalCmdType() != None

    def isKilledJob(self):
        return self.killed_job
      
    def getKilledLogfile(self):
        return self.killed_logfile
       
    def setKilledJobState(self):
        self.killed_job = True
        self.killed_logfile = self.current_logfile

    def resetKilledJobState(self):
        self.killed_job = False
        self.killed_logfile = None

    def getJobStatus(self):
        if self.current_cmd_type != None:
            return {"job": self.current_cmd_type, "type": "daemon", "started": self.current_started.astimezone().isoformat() if self.current_started else None}
        external_cmd = self.external_cmd_type
        if external_cmd != None:
            return {"job": external_cmd, "type": "manual", "started": None}

        return {"job": None, "type": None, "started": None}

    def restoreLock(self,cmd_type,start_time,file_name):
        self.current_cmd_type = cmd_type
        self.current_started = start_time
        self.current_logfile = file_name

        self.handler.notifyExecutorJobStatus(self.getJobStatus())
        
    def lock(self, cmd_type, file_name):
        if self.current_started != None:
            return False
        else:
            self.current_cmd_type = cmd_type
            self.current_started = datetime.now()
            self.current_logfile = file_name

            self.resetKilledJobState()

            self.handler.notifyExecutorJobStatus(self.getJobStatus())
            return True

    def _unlock(self, exit_code):
        self.initJobs()

        #status = self.getJobStatus()
        #status["state"] = "finished"
        #status["finished"] = datetime.now().astimezone().isoformat()
        #status["exit_code"] = exit_code

        self.current_cmd_type = None
        self.current_started = None
        self.current_logfile = None
        self.current_child = None

        self.handler.notifyExecutorJobStatus(self.getJobStatus())

    def finishRun(self, job_log_file, exit_status, start_time, cmd_type, username):
        duration = datetime.now() - start_time
        start_time_str = start_time.strftime(CmdExecuter.START_TIME_STR_FORMAT)
        status_msg = "success" if exit_status == 0 else "failed"
        finished_log_name = u"{}-{}-{}-{}-{}.log".format(start_time_str,round(duration.total_seconds(),1),status_msg, cmd_type,username)
        finished_log_file = u"{}{}".format(config.job_log_folder,finished_log_name)

        os.rename(job_log_file, finished_log_file)
        self.current_logfile = finished_log_name
        self._unlock(exit_status)

    def initLogFilename(self, cmd_block):
        username = cmd_block["username"]
        cmd_type = cmd_block["cmd_type"]
        
        start_time = datetime.now()
        start_time_str = start_time.strftime(CmdExecuter.START_TIME_STR_FORMAT)
        job_log_name = u"{}-{}-{}-{}-{}.log".format(start_time_str,0,"running", cmd_type,username)
        job_log_file = u"{}{}".format(config.job_log_folder,job_log_name)
        
        return [start_time, job_log_name, job_log_file]

    def logInterruptedCmd(self, lf, msg ):
        # no need for a newline for interruptable commands
        lf.write(msg)

    def runFunction(self,cmd_type, _cmd, lf):
        name = _cmd["function"]
      
        msg = u"Run function '{}' - '{}'".format(cmd_type, name)
        logging.info(msg)
        lf.write(u"{}\n".format(msg))

        function = self.handler
        for part in name.split("."):
            function = getattr(function, part )
        function()
        
        return 0

    def runCmd(self,cmd_type, _cmd, lf):
        start_time = datetime.now()
        
        cmd = _cmd["cmd"]
        interaction = _cmd["interaction"]
        cwd = _cmd["cwd"]
        env = _cmd["env"]

        msg = u"Start cmd '{}' - '{}'".format(cmd_type, cmd)
        logging.info(msg)
        lf.write(u"{}\n".format(msg))
        lf.getFile().write("\n")
        lf.getFile().flush()
        
        if env is None:
            env = {}
        env["PATH"] = CmdExecuter.env_path
        env["HOME"] = CmdExecuter.home_path

        self.current_child = child = pexpect.spawn(cmd, timeout=3600, cwd=cwd, env=env)
        child.logfile_read = lf
        
        if interaction is not None:
            patterns = list(interaction.keys())
            responses = list(interaction.values())
        else:
            patterns = None
            responses = None
            
        while child.isalive():
            try:
                index = child.expect(patterns)
                child.sendline(responses[index])
            except TIMEOUT:
                break
            except EOF:
                break

        child.close()
        exit_status = child.exitstatus

        delta = datetime.now() - start_time
        delta = delta - timedelta(microseconds = delta.microseconds)
        duration = str(delta)

        if self.isInterruptableJob(cmd_type):
            if exit_status is None: # can happen if service process get killed as part of interruptable job
                exit_status = 0
        else:
            lf.getFile().write("\n")
            if exit_status == 0:
                lf.write("The command exited successful after {}\n".format(duration))

        if exit_status != 0:
            lf.write("The command exited with {} (unsuccessful) after {}\n".format(exit_status,duration))
            
        return exit_status
        
    def processCmdBlock(self,cmd_block,lf):
        exit_status = 1
        
        step = None
        cmd_type = cmd_block["cmd_type"]
        try:
            for _cmd in cmd_block["cmds"]:
                if exit_status == 0:
                    lf.getFile().write("\n")
                    
                if "function" in _cmd:
                    step = _cmd["function"]
                    exit_status = self.runFunction(cmd_type,_cmd,lf)
                else:
                    step = _cmd["cmd"]
                    exit_status = self.runCmd(cmd_type,_cmd,lf)
                
                if exit_status != 0:
                    break

        except ValueError:
            #logging.warn(traceback.format_exc())
            pass
        except Exception as e:
            exit_status = 1
            logging.error(traceback.format_exc())
            ex_type, ex_value, ex_traceback = sys.exc_info()
            lf.write("The command '{}' - '{}' exited with '{}: {}'.\n".format(cmd_type,step,type(e).__name__,ex_value))
            
        return exit_status

    def killProcess(self):
        child = self.current_child
        if child is not None:
            self.setKilledJobState()
            returncode = subprocess.call(['sudo', 'kill', str(child.pid)])
            return returncode
        return 0
    
    def _checkExternalCmdTypes(self):
        while self.is_running:
            self._refreshExternalCmdType()
            threading.Event()
            self.event.wait( 1 if self.handler.areSocketClientsActive() else 60)
            self.event.clear()

    def _refreshExternalCmdType(self): 
        #start = time.time()

        notifyJobStatus = False
        if not self.isDaemonJobRunning():
            if self.external_cmd_type_pid is None or not processlist.Processlist.checkPid(self.external_cmd_type_pid):

                external_cmd_type = None
                external_cmd_type_pid = None

                # 10 times faster then processlist.Processlist.getPids(" |".join( CmdExecuter.process_mapping.keys()))
                current_pids = processlist.Processlist.getPids()
                if current_pids is not None and current_pids != self.current_pids:
                    for pid in set(current_pids) - set(self.current_pids):
                        cmdline = processlist.Processlist.getCmdLine(pid)
                        if not cmdline:
                            continue
                        for term in CmdExecuter.process_mapping:
                            if "{} ".format(term) in cmdline and not self.operating_system.isRunning(cmdline):
                                external_cmd_type_pid = pid
                                external_cmd_type = CmdExecuter.process_mapping[term]
                                break
                        if external_cmd_type is not None:
                            break
                        #logging.info("check {} {}".format(pid,cmdline))
                    self.current_pids = current_pids

                #pids = processlist.Processlist.getPids(" |".join( CmdExecuter.process_mapping.keys()))
                #if pids is not None:
                #    for pid in pids:
                #        cmdline = processlist.Processlist.getCmdLine(pid)
                #        if cmdline is not None:
                #            for term in CmdExecuter.process_mapping:
                #                if "{} ".format(term) in cmdline:
                #                    external_cmd_type_pid = pid
                #                    external_cmd_type = CmdExecuter.process_mapping[term]
                #                    break
                #            if external_cmd_type is not None:
                #                break
                
                if external_cmd_type is None and self.external_cmd_type is not None:
                    self.process_watcher.refresh()

                if external_cmd_type != self.external_cmd_type:
                    notifyJobStatus = True

                self.external_cmd_type = external_cmd_type
                self.external_cmd_type_pid = external_cmd_type_pid
            else:
                self.current_pids = []
        else:
            if self.external_cmd_type is not None:
                self.process_watcher.refresh()
                notifyJobStatus = True

            self.external_cmd_type = None
            self.external_cmd_type_pid = None
            self.current_pids = []

        #end = time.time()
        #logging.info("processlist: {}".format(end-start))

        if notifyJobStatus:
            self.handler.notifyExecutorJobStatus(self.getJobStatus())

    def triggerSocketClientsActive(self):
        self.event.set()

    def getExternalCmdType(self, refresh = True):
        if refresh:
            self._refreshExternalCmdType()
        return self.external_cmd_type
