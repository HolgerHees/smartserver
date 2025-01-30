import sys
import os
import subprocess
import traceback
import glob
import threading
import logging

import time

from datetime import datetime, timedelta

from config import config

from smartserver import command
from smartserver import pexpect
from smartserver import processlist
from smartserver.metric import Metric

from server.watcher import watcher


class CmdExecuter(watcher.Watcher): 
    START_TIME_STR_FORMAT = "%Y.%m.%d_%H.%M.%S"

    env_path = "/sbin:/usr/sbin:/usr/local/sbin:/usr/local/bin:/usr/bin:/bin"
    home_path = "/root"

    def __init__(self, handler, process_watcher):
        super().__init__()
      
        self.handler = handler
        self.process_watcher = process_watcher

        self.current_cmd_type = None
        self.current_started = None
        self.current_logfile = None
        self.current_child = None

        self.external_cmd_type = None
        
        self.jobs = []
        self.initJobs()

        self.is_running = True
        self.event = threading.Event()
        self.extern_cmd_lock = threading.Lock()
        self.thread = threading.Thread(target=self._checkExternalCmdTypes, args=())

    def start(self):
        self.thread.start()

    def terminate(self):
        self.is_running = False
        self.event.set()
        self.thread.join()
            
    def isInterruptiveJob(self,cmd_type):
        return cmd_type in [ "system_reboot", "daemon_restart" ]

    def initJobs(self):
        _jobs = []
        
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
            job["user"] = data[4][:-4];
            _jobs.append(job)
            
        self.jobs = _jobs;

        self.handler.notifyChangedCmdExecuterJobsRefreshed(self.jobs)

    def getJobs(self):
        return self.jobs

    def getCurrentJobStarted(self):
        return self.current_started
      
    def getCurrentJobLogfile(self):
        return self.current_logfile
      
    def getCurrentJobCmdType(self):
        return self.current_cmd_type

    def isRunning(self, check_global_running):
        if self.current_cmd_type != None:
            return True

        return self.getExternalCmdType() != None if check_global_running else False

    def getJobStatus(self):
        if self.current_cmd_type != None:
            return {"job": self.current_cmd_type, "type": "daemon", "started": self.current_started.astimezone().isoformat() if self.current_started else None}
        if self.external_cmd_type != None:
            return {"job": self.external_cmd_type, "type": "manual", "started": None}
        return {"job": None, "type": None, "started": None}

    def restoreLock(self,cmd_type,start_time,file_name):
        self.current_cmd_type = cmd_type
        self.current_started = start_time
        self.current_logfile = file_name

        self.handler.notifyChangedCmdExecuterJobState(self.getJobStatus())
        
    def lock(self, cmd_type, file_name):
        if self.current_started != None:
            return False
        else:
            self.current_cmd_type = cmd_type
            self.current_started = datetime.now()
            self.current_logfile = file_name

            self.handler.notifyChangedCmdExecuterJobState(self.getJobStatus())
            return True

    def _unlock(self, exit_code):

        #status = self.getJobStatus()
        #status["state"] = "finished"
        #status["finished"] = datetime.now().astimezone().isoformat()
        #status["exit_code"] = exit_code

        self.current_cmd_type = None
        self.current_started = None
        self.current_logfile = None
        self.current_child = None

        self.handler.notifyChangedCmdExecuterJobState(self.getJobStatus())

    def finishRun(self, job_log_file, exit_status, start_time, cmd_type, username):
        if self.current_child is not None and self.current_child.isTerminated():
            state = "stopped"
        else:
            state = "success" if exit_status == 0 else "failed"

        start_time_str = start_time.strftime(CmdExecuter.START_TIME_STR_FORMAT)

        duration = datetime.now() - start_time
        finished_log_name = CmdExecuter._getLogFilename(start_time_str, round(duration.total_seconds(),1), state, cmd_type, username)
        finished_log_file = u"{}{}".format(config.job_log_folder,finished_log_name)

        notification_topic = CmdExecuter.getTopicName(start_time_str, cmd_type, username)
        self.handler.notifyChangedCmdExecuterState(state, notification_topic)

        os.rename(job_log_file, finished_log_file)
        self.current_logfile = finished_log_name
        self._unlock(exit_status)

        self.initJobs()

        return state

    def initLogFilename(self, cmd_block):
        username = cmd_block["username"]
        cmd_type = cmd_block["cmd_type"]
        
        start_time = datetime.now()
        start_time_str = start_time.strftime(CmdExecuter.START_TIME_STR_FORMAT)

        job_log_name = CmdExecuter._getLogFilename(start_time_str, 0, "running", cmd_type, username)
        job_log_file = u"{}{}".format(config.job_log_folder,job_log_name)
        
        return [start_time, start_time_str, job_log_name, job_log_file]

    def logInterruptedCmd(self, lf, msg ):
        # no need for a newline for interruptable commands
        lf.writeLine(msg)

    def runFunction(self,cmd_type, _cmd, lf):
        name = _cmd["function"]
      
        msg = u"Run function '{}' - '{}'".format(cmd_type, name)
        logging.info(msg)
        lf.writeLine(u"{}".format(msg))

        function = self.handler
        for part in name.split("."):
            function = getattr(function, part )

        if "args" in _cmd:
            function(*_cmd["args"], **_cmd["kwargs"])
        else:
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
        lf.writeLine(u"{}".format(msg))
        lf.writeRaw("\n")
        
        if env is None:
            env = {}
        env["PATH"] = CmdExecuter.env_path
        env["HOME"] = CmdExecuter.home_path

        self.current_child = pexpect.Process(cmd, timeout=3600, logfile=lf, cwd=cwd, env=env, interaction=interaction)
        self.current_child.start()
        exit_status = self.current_child.getExitCode()
        #if exit_status != 0 and self.current_child.isTerminated():
        #    exit_status = 0

        delta = datetime.now() - start_time
        delta = delta - timedelta(microseconds = delta.microseconds)
        duration = str(delta)

        if self.isInterruptiveJob(cmd_type):
            if exit_status is None: # can happen if service process get killed as part of interruptable job
                exit_status = 0
        else:
            if exit_status == 0:
                self._writeWrapppedLog(lf, "The command exited successful after {}".format(duration))

        if self.current_child.isTerminated():
            self._writeWrapppedLog(lf, "The command was stopped after {}".format(duration))
        elif exit_status != 0:
            self._writeWrapppedLog(lf, "The command exited with {} (unsuccessful) after {}".format(exit_status,duration))
            
        return exit_status
        
    def processCmdBlock(self,cmd_block,lf):
        exit_status = 1
        
        step = None
        cmd_type = cmd_block["cmd_type"]
        try:
            for _cmd in cmd_block["cmds"]:
                if exit_status == 0:
                    lf.writeRaw("\n")
                    
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
            self._writeWrapppedLog(lf, "The command '{}' - '{}' exited with '{}: {}'.".format(cmd_type,step,type(e).__name__,ex_value))
            
        return exit_status

    def killProcess(self):
        if self.current_child is not None:
            self.current_child.terminate()
    
    def _checkExternalCmdTypes(self):
        logging.info("CmdExecuter started")

        try:
            while self.is_running:
                self._refreshExternalCmdType()
                self.event.wait( 1 if self.handler.isHightAccuracy() else 60)
                self.event.clear()
        except Exception as e:
            self.is_running = False
            raise e
        finally:
            logging.info("CmdExecuter stopped")

    def _refreshExternalCmdType(self):
        with self.extern_cmd_lock:
            external_cmd_type = self.process_watcher.refreshExternalCmdType()
            if self.external_cmd_type != external_cmd_type:
                self.external_cmd_type = external_cmd_type
                self.handler.notifyChangedCmdExecuterJobState(self.getJobStatus())
                self.handler.notifyChangedExternalCmdState()

    def getExternalCmdType(self, refresh=True):
        if refresh:
            self._refreshExternalCmdType()
        return self.external_cmd_type

    def triggerHighAccuracy(self):
        self.event.set()

    def _writeWrapppedLog(self, lf, msg):
        lf.writeRaw("\n")
        lf.writeLine(msg)

    @staticmethod
    def _getLogFilename(time_str, duration, state, cmd_type, username ):
        return u"{}-{}-{}-{}-{}.log".format(time_str, duration, state, cmd_type, username)

    @staticmethod
    def getTopicName(time_str, cmd_type, username):
        return u"{}-{}-{}".format(time_str,cmd_type,username)

    @staticmethod
    def getLogfiles(log_folder, time_str, cmd_type, username):
        logfilename = CmdExecuter._getLogFilename(time_str, '*', '*', cmd_type, username)
        return glob.glob("{}{}".format(log_folder, logfilename));

    @staticmethod
    def getLogFileDetails(filename):
        data = os.path.basename(filename).split("-")

        timestamp = datetime.strptime(data[0],"%Y.%m.%d_%H.%M.%S").timestamp()
        return {
            "date": data[0],
            "duration": data[1],
            "state": data[2],
            "cmd": data[3],
            "username": data[4][:-4],
            "timestamp": timestamp
        }

    def getStateMetrics(self):
        return [
            Metric.buildProcessMetric("update_service", "cmd_executer", "1" if self.is_running else "0")
        ]
