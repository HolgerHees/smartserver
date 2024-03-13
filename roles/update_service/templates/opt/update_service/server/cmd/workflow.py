import glob

import threading
import json
import os
import time
import logging

from datetime import datetime, timezone

from config import config
from server.cmd.executer import CmdExecuter

from smartserver.logfile import LogFile

MAX_DAEMON_RESTART_TIME = 30
MAX_SYSTEM_REBOOT_TIME = 600

MIN_PROCESS_INACTIVITY_TIME = 30

MIN_STARTUP_WAITING_TIME = 30
MAX_STARTUP_WAITING_TIME = 1800

MIN_WORKFLOW_WAITING_TIME = 0
MAX_WORKFLOW_WAITING_TIME = 1800


class CmdWorkflow: 
    STATE_DONE = "done"
    STATE_RUNNING = "running"
    STATE_WAITING = "waiting"
    STATE_KILLED = "killed"
    STATE_STOPPED = "stopped"

    STATE_CHECK_WRONG_SYSTEM_UPDATE_STATE = "wrong_system_update_hash"
    STATE_CHECK_WRONG_SMARTSERVER_UPDATE_STATE = "wrong_smartserver_update_hash"

    def __init__(self,handler, cmd_executer, cmd_builder ):
        self.handler = handler
        self.cmd_executer = cmd_executer
        self.cmd_builder = cmd_builder
        
        self.workflow_state = CmdWorkflow.STATE_DONE

    def handleRunningStates(self):
        thread = threading.Thread(target=self._handleRunningStates, args=())
        thread.start()

    def _handleRunningStates(self):
        for log_file in glob.glob(u"{}*-*-running-*-*.log".format(config.job_log_folder)):
            log_details = CmdExecuter.getLogFileDetails(log_file)
            result = False
            if self.cmd_executer.isInterruptiveJob(log_details["cmd"]):
                result = self._checkWorkflow(log_details, log_file)
                if type(result) != bool:
                    self._handleWorkflow(result, log_details, log_file)
            else:
                result = self._handleCrash(log_file, log_details)

            if type(result) == bool:
                logging.info("Mark job '{}' as '{}'".format(log_details["cmd"], 'success' if result else 'failed'))
         
        if os.path.isfile(config.deployment_workflow_file):
            os.unlink(config.deployment_workflow_file)

    def _handleCrash(self,log_file, log_details):
        with self._initLog( log_file, 'a', log_details["date"], log_details["cmd"], log_details["username"], None) as lf:
            lf.writeRaw("\n")
            lf.writeLine("The command crashed, because logfile was still marked as running.")

        os.rename(log_file, log_file.replace("-running-","-crashed-"))
        
        return False

    def _checkWorkflow(self, log_details, log_file):
        start_time_str = log_details["date"]
        expected_workflow = log_details["cmd"]

        is_system_reboot = expected_workflow == "system_reboot"

        log_mtime = os.stat(log_file).st_mtime
        log_modified_time = datetime.fromtimestamp(log_mtime, tz=timezone.utc)
        log_file_age = datetime.now().timestamp() - log_modified_time.timestamp()
        
        max_log_file_age = MAX_SYSTEM_REBOOT_TIME if is_system_reboot else MAX_DAEMON_RESTART_TIME
        is_success = log_file_age < max_log_file_age
        
        flag = "success"
        if is_success:
            if os.path.isfile(config.deployment_workflow_file):
                with open(config.deployment_workflow_file, 'r') as f:
                    workflow = json.load(f)
                    if workflow[0]["cmd_type"] == expected_workflow:
                        return workflow
                    else:
                        msg = "Can't continue with workflow. Wrong first workflow. Expected: '{}' - Found: '{}'\n".format(expected_workflow,workflow[0]["cmd_type"])
                        flag = "failed"
                        is_success = False
            else:
                msg = "Can't continue with workflow. Missing workflow file\n"
                flag = "failed"
                is_success = False
        else:
            msg = "The command crashed, because logfile was too old.\n"
            flag = "crashed"

        with self._initLog( log_file, 'a', log_details["date"], log_details["cmd"], log_details["username"], "running") as lf:
            self.cmd_executer.logInterruptedCmd(lf, msg)
            
        os.rename(log_file, log_file.replace("-running-", "-{}-".format(flag)))
        
        return is_success

    def _handleWorkflow(self, workflow, log_details, log_file):
        thread = threading.Thread(target=self._resumeWorkflow, args=(workflow, log_details, log_file ))
        thread.start()
        
    def _waitToProceed(self, lf, min_process_inactivity_time, min_waiting_time, max_waiting_time, suffix ):
        if min_waiting_time == 0 and self.cmd_executer.getExternalCmdType() == None:
            return True
        
        msg = "Waiting a maximum of {}s for {}s of inactivity to {}".format(max_waiting_time, min_process_inactivity_time, suffix)
        logging.info(msg)
        self.cmd_executer.logInterruptedCmd(lf, "{}\n".format(msg))

        can_proceed = False
        waiting_start = datetime.now().timestamp()
        last_seen_time = waiting_start
        last_log_time = waiting_start
        last_cmd_type = None
        pre_workflow_state = self.workflow_state
        self.workflow_state = CmdWorkflow.STATE_WAITING
        while self.workflow_state == CmdWorkflow.STATE_WAITING:
            now = datetime.now().timestamp()
            inactivity_time = now - last_seen_time
            waiting_time = round(now - waiting_start)
            
            external_cmd_type = self.cmd_executer.getExternalCmdType()
            if external_cmd_type != None:
                last_seen_time = now
                last_cmd_type = external_cmd_type if external_cmd_type is not None else self.cmd_executer.getCurrentJobCmdType()

            if waiting_time > min_waiting_time and inactivity_time > min_process_inactivity_time:
                can_proceed = True
                break

            if waiting_time > max_waiting_time:
                msg = "Not able to proceed due still running '{}'".format(last_cmd_type)
                logging.info(msg)
                self.cmd_executer.logInterruptedCmd(lf, "{}\n".format(msg))
                break
                
            if round(now - last_log_time) >= 15:
                last_log_time = now
                if last_cmd_type != None:
                    cmd_msg = " - Last run of '{}' {}s ago".format(last_cmd_type,round(inactivity_time))
                else:
                    cmd_msg = ""
                
                msg = "Waiting since {}s for {}s of inactivity{}".format(round(waiting_time), min_process_inactivity_time, cmd_msg)
                logging.info(msg)
                self.cmd_executer.logInterruptedCmd(lf, "{}\n".format(msg))
                
            time.sleep(2)
        if self.workflow_state == CmdWorkflow.STATE_WAITING:
            self.workflow_state = pre_workflow_state

        return can_proceed

    def _preWorkflow(self, workflow):
        self.workflow_state = CmdWorkflow.STATE_RUNNING
        self.handler.notifyWorkflowState()
        return 1 if len(workflow) > 0 else 0

    def _pastWorkflow(self, exit_code):
        if self.workflow_state == CmdWorkflow.STATE_RUNNING:
            self.workflow_state = CmdWorkflow.STATE_DONE if exit_code == 0 else CmdWorkflow.STATE_STOPPED
        self.handler.notifyWorkflowState()

    def _resumeWorkflow(self,workflow, log_details, log_file):
        exit_code = self._preWorkflow(workflow)

        start_time = datetime.strptime(log_details["date"], CmdExecuter.START_TIME_STR_FORMAT)
        with self._initLog( log_file, 'a', log_details["date"], log_details["cmd"], log_details["username"], "running") as lf:
            cmd_block = workflow.pop(0)
            self.cmd_executer.restoreLock(cmd_block["cmd_type"],start_time,os.path.basename(log_file))

            if len(cmd_block["cmds"]) > 0 or len(workflow) > 0:
                can_proceed = self._waitToProceed(lf, MIN_PROCESS_INACTIVITY_TIME, MIN_STARTUP_WAITING_TIME, MAX_STARTUP_WAITING_TIME, "resume")
            else:
                can_proceed = True
                    
            if can_proceed:
                has_cmds = len(cmd_block["cmds"]) > 0

                logging.info("{} '{}'".format( "Proceed with" if has_cmds else "Finish job", cmd_block["cmd_type"]))
                self.cmd_executer.logInterruptedCmd(lf, "'{}' was successful\n".format(cmd_block["cmd_type"]))
            
                # system reboot has only one cmd, means after reboot 'cmds' is empty
                exit_code = self.cmd_executer.processCmdBlock(cmd_block,lf) if has_cmds else 0
            else:
                exit_code = -1

        self.cmd_executer.finishRun(log_file,exit_code,start_time,cmd_block["cmd_type"],cmd_block["username"])
                      
        if exit_code == 0 and len(workflow) > 0:
            self._runWorkflow(workflow)
        else:
            self._pastWorkflow(exit_code)

    def _runWorkflow(self, workflow):
        exit_code = self._preWorkflow(workflow)

        while len(workflow) > 0:
            cmd_block = workflow.pop(0)
            
            # ***** ANALYSE *****
            if "function" in cmd_block:
                function = self.handler
                for part in cmd_block["function"].split("."):
                    function = getattr(function, part )

                _cmd_block = function(cmd_block["username"], cmd_block["params"])
                if _cmd_block is None:
                    logging.info("Skip workflow function '{}'".format(cmd_block["function"]))
                    continue
                elif type(_cmd_block) == bool:
                    if _cmd_block:
                        continue
                    else:
                        self.workflow_state = CmdWorkflow.STATE_STOPPED
                        break
                elif type(_cmd_block) == str:
                    self.workflow_state = _cmd_block
                    break
                else:
                    logging.info("Run Workflow function '{}'".format(cmd_block["function"]))
                    cmd_block = _cmd_block

            # ***** PREPARE *****
            is_interuptive_workflow = self.cmd_executer.isInterruptiveJob(cmd_block["cmd_type"])

            if is_interuptive_workflow:
                first_cmd = cmd_block["cmds"].pop(0)

                workflow.insert(0,cmd_block)
                    
                with open(config.deployment_workflow_file, 'w') as f:
                    json.dump(workflow, f)
                    
                cmd_block = self.cmd_builder.buildCmdBlock(cmd_block["username"], cmd_block["cmd_type"], [first_cmd])

                #if cmd_block["cmd_type"] == "system_reboot":
                #    self._prepareTestWorkflow(cmd_block)
              
            # ***** RUN CMD *****
            [start_time, start_time_str, log_name, log_file ] = self.cmd_executer.initLogFilename(cmd_block)

            with self._initLog( log_file, 'w', start_time_str, cmd_block["cmd_type"], cmd_block["username"], "running") as lf:
                can_proceed = self._waitToProceed(lf, MIN_PROCESS_INACTIVITY_TIME, MIN_WORKFLOW_WAITING_TIME, MAX_WORKFLOW_WAITING_TIME, "proceed")
                finish_run = False
                if can_proceed:
                    if self.cmd_executer.lock(cmd_block["cmd_type"], log_name):
                        exit_code = self.cmd_executer.processCmdBlock(cmd_block, lf)
                        finish_run = cmd_block["cmd_type"] != "system_reboot"
                    else:
                        self.cmd_executer.logInterruptedCmd(lf, "'{}' not able to lock\n".format(cmd_block["cmd_type"]))
                        exit_code = -1
                        finish_run = True
                else:
                    exit_code = -1
                    finish_run = True

                if finish_run:
                    self.cmd_executer.finishRun(log_file, exit_code, start_time, cmd_block["cmd_type"] ,cmd_block["username"])
                
            # ***** FINALIZE *****
            if exit_code != 0 or self.workflow_state != CmdWorkflow.STATE_RUNNING:
                if os.path.isfile(config.deployment_workflow_file):
                    os.unlink(config.deployment_workflow_file)
                if self.workflow_state != CmdWorkflow.STATE_KILLED:
                    logging.error("Command '{}' exited with code '{}'".format(cmd_block["cmd_type"],exit_code));
                break
          
            if is_interuptive_workflow:
                break

        self._pastWorkflow(exit_code)

    def runWorkflow(self, workflow, check_global_running ):
        if not self.cmd_executer.isRunning(check_global_running):
            thread = threading.Thread(target=self._runWorkflow, args=(workflow,))
            thread.start()
            return True
        else:
            return False
            
    def killWorkflow(self):
        self.cmd_executer.killProcess()
        self.workflow_state = CmdWorkflow.STATE_KILLED
        #self.handler.notifyWorkflowState()
        
    def getWorkflowState(self):
        return self.workflow_state

    def isWorkflowActive(self):
        return self.workflow_active

    def _initLog(self, log_file, mode, start_time_str, cmd, username, state):
        notification_topic = CmdExecuter.getTopicName(start_time_str, cmd, username)
        if state is not None:
            self.handler.notifyChangedCmdExecuterState(state, notification_topic)
        return LogFile(log_file, mode, self.handler.notifyChangedCmdExecuterLog, notification_topic)

    def _prepareTestWorkflow(self,cmd_block):
        for cmd in cmd_block["cmds"]:
            interaction = cmd["interaction"]
            cmd["interaction"] = "****" if interaction else interaction
            cmd["cmd"] = "/*" + cmd["cmd"] + "*/ => sleep 5"
            logging.info(cmd)
            cmd["interaction"] = interaction
            cmd["cmd"] = "sleep 5"
