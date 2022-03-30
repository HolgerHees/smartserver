import glob

import threading
import json
import os
import time

from datetime import datetime, timezone

from config import config
from server.cmd.executer import CmdExecuter

from smartserver.logfile import LogFile

MAX_DAEMON_RESTART_TIME = 30
MAX_SYSTEM_REBOOT_TIME = 600

MIN_PROCESS_INACTIVITY_TIME = 30
MAX_STARTUP_WAITING_TIME = 1200


class CmdWorkflow: 
    def __init__(self,logger, handler, cmd_executer, cmd_builder ):
        self.logger = logger
        self.handler = handler
        self.cmd_executer = cmd_executer
        self.cmd_builder = cmd_builder
        
        self.workflow_state = None

    def handleRunningStates(self):
        thread = threading.Thread(target=self._handleRunningStates, args=())
        thread.start()

    def _handleRunningStates(self):
        for name in glob.glob(u"{}*-*-running-*-*.log".format(config.job_log_folder)):
            name_parts = os.path.basename(name).split("-")
            
            result = False
            if self.cmd_executer.isInterruptableJob(name_parts[3]):
                result = self._checkWorkflow(name,name_parts[0],name_parts[3])
                if type(result) != bool:
                    self._handleWorkflow(result,name,name_parts[0])
            else:
                result = self._handleCrash(name)

            if type(result) == bool:
                self.logger.info("Mark job '{}' as '{}'".format(name_parts[3], 'success' if result else 'failed'))
         
        if os.path.isfile(config.deployment_workflow_file):
            os.unlink(config.deployment_workflow_file)

    def _handleCrash(self,file_name):
        with open(file_name, 'a') as f:
            lf = LogFile(f)
            lf.getFile().write("\n")
            lf.write("The command crashed, because logfile was still marked as running.\n")

        os.rename(file_name, file_name.replace("-running-","-crashed-"))
        
        return False

    def _checkWorkflow(self,log_file_name,start_time_str,expected_workflow):
        is_system_reboot = expected_workflow == "system_reboot"

        log_mtime = os.stat(log_file_name).st_mtime
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

        with open(log_file_name, 'a') as f:
            lf = LogFile(f)
            self.cmd_executer.logInterruptedCmd(lf, msg)
            
        os.rename(log_file_name, log_file_name.replace("-running-", "-{}-".format(flag)))
        
        return is_success

    def _handleWorkflow(self,workflow,log_file_name,start_time_str):
        thread = threading.Thread(target=self._proceedWorkflow, args=(workflow, log_file_name, start_time_str ))
        thread.start()

    def _proceedWorkflow(self,workflow, log_file_name, start_time_str):
        start_time = datetime.strptime(start_time_str, CmdExecuter.START_TIME_STR_FORMAT) 

        exit_code = 1
        with open(log_file_name, 'a') as f:
            cmd_block = workflow.pop(0)

            self.cmd_executer.restoreLock(cmd_block["cmd_type"],start_time,log_file_name)
            lf = LogFile(f)

            if len(cmd_block["cmds"]) > 0 or len(workflow) > 0:
                msg = "Waiting for {}s of inactivity to proceed".format(MIN_PROCESS_INACTIVITY_TIME)
                self.logger.info(msg)
                self.cmd_executer.logInterruptedCmd(lf, "{}\n".format(msg))

                can_proceed = False
                waiting_start = datetime.now().timestamp()
                last_seen_time = waiting_start
                last_log_time = waiting_start
                last_cmd_type = None
                while True:
                    now = datetime.now().timestamp()
                    inactivity_time = now - last_seen_time
                    waiting_time = round(now - waiting_start)
                    
                    active_cmd_type = self.cmd_executer.getExternalCmdType()
                    if active_cmd_type != None:
                        last_seen_time = now
                        last_cmd_type = active_cmd_type

                    if inactivity_time > MIN_PROCESS_INACTIVITY_TIME:
                        can_proceed = True
                        break

                    if waiting_time > MAX_STARTUP_WAITING_TIME:
                        msg = "Not able to proceed due still running '{}'".format(last_cmd_type)
                        self.logger.info(msg)
                        self.cmd_executer.logInterruptedCmd(lf, "{}\n".format(msg))
                        break
                      
                    if round(now - last_log_time) >= 15:
                        last_log_time = now
                        if last_cmd_type != None:
                            cmd_msg = " - Last run of '{}' {}s ago".format(last_cmd_type,round(inactivity_time))
                        else:
                            cmd_msg = ""
                      
                        msg = "Waiting since {}s for {}s of inactivity{}".format(round(waiting_time), MIN_PROCESS_INACTIVITY_TIME, cmd_msg)
                        self.logger.info(msg)
                        self.cmd_executer.logInterruptedCmd(lf, "{}\n".format(msg))
                        
                    time.sleep(2)
            else:
                can_proceed = True
                    
            if can_proceed:
                has_cmds = len(cmd_block["cmds"]) > 0

                self.logger.info("{} '{}'".format( "Proceed with" if has_cmds else "Finish job", cmd_block["cmd_type"]))
                self.cmd_executer.logInterruptedCmd(lf, "'{}' was successful\n".format(cmd_block["cmd_type"]))
            
                # system reboot has only one cmd, means after reboot 'cmds' is empty
                exit_code = self.cmd_executer.processCmdBlock(cmd_block,lf) if has_cmds else 0
                 
        self.cmd_executer.finishRun(log_file_name,exit_code,start_time,start_time_str,cmd_block["cmd_type"],cmd_block["username"])
                      
        if exit_code == 0 and len(workflow) > 0:
            if not self.runWorkflow(workflow, True):
                self.logger.error("Can't continue with workflow due a still running process");
        
    def runWorkflow(self, workflow, checkGlobalRunning ):
        isRunning = self.cmd_executer.isRunning() if checkGlobalRunning else self.cmd_executer.isDaemonJobRunning()
        if not isRunning :
            thread = threading.Thread(target=self._runWorkflow, args=(workflow, checkGlobalRunning ))
            thread.start()
            time.sleep(0.5)
            
            return True
        else:
            return False

    def _runWorkflow(self, workflow, checkGlobalRunning):   
        self.workflow_state = None

        while len(workflow) > 0:
            cmd_block = workflow.pop(0)
            if "function" in cmd_block:
                function = self.handler
                for part in cmd_block["function"].split("."):
                    function = getattr(function, part )

                _cmd_block = function(cmd_block["username"], cmd_block["params"])
                if _cmd_block is None:
                    self.logger.info("Skip workflow function '{}'".format(cmd_block["function"]))
                    continue
                elif type(_cmd_block) == bool:
                    if _cmd_block:
                        continue
                    else:
                        self.workflow_state = "stopped"
                        break
                elif type(_cmd_block) == str:
                    self.workflow_state = _cmd_block
                    break
                else:
                    self.logger.info("Run Workflow function '{}'".format(cmd_block["function"]))
                    cmd_block = _cmd_block

            is_interuptable_workflow = self.cmd_executer.isInterruptableJob(cmd_block["cmd_type"])

            if is_interuptable_workflow:
                first_cmd = cmd_block["cmds"].pop(0)

                workflow.insert(0,cmd_block)
                    
                with open(config.deployment_workflow_file, 'w') as f:
                    json.dump(workflow, f)
                    
                cmd_block = self.cmd_builder.buildCmdBlock(cmd_block["username"], cmd_block["cmd_type"], [first_cmd])

                #if cmd_block["cmd_type"] == "system_reboot":
                #    self._prepareTestWorkflow(cmd_block)
              
            isRunning = self.cmd_executer.isRunning() if checkGlobalRunning else self.cmd_executer.isDaemonJobRunning()
            if not isRunning and self.cmd_executer.lock(cmd_block["cmd_type"]):
                exit_code = self.cmd_executer.runCmdBlock(cmd_block)
            else:
                self.cmd_executer.interruptedCmdBlock(cmd_block)
                exit_code = -1
                
            if exit_code != 0 or self.workflow_state is not None:
                if os.path.isfile(config.deployment_workflow_file):
                    os.unlink(config.deployment_workflow_file)
                    
                if self.cmd_executer.isKilledJob():
                    logfile = self.cmd_executer.getKilledLogfile()
                    if logfile:
                        filedata = os.path.basename(logfile).split("-")
                        files = glob.glob(u"{}{}-*-*-{}-{}".format(config.job_log_folder,filedata[0],filedata[3],filedata[4]))
                        for filename in files:
                            os.rename(filename, filename.replace("-failed-","-stopped-"))
                        self.cmd_executer.resetKilledJobState()
                else:
                    self.logger.error("Command '{}' exited with code '{}'".format(cmd_block["cmd_type"],exit_code));
                break
          
            if is_interuptable_workflow:
                break
            
    def killWorkflow(self):
        self.cmd_executer.killProcess()
        self.workflow_state = "killed"
        
    def getWorkflowState(self):
        return self.workflow_state
        
    def _prepareTestWorkflow(self,cmd_block):
        for cmd in cmd_block["cmds"]:
            interaction = cmd["interaction"]
            cmd["interaction"] = "****" if interaction else interaction
            cmd["cmd"] = "/*" + cmd["cmd"] + "*/ => sleep 5"
            self.logger.info(cmd)
            cmd["interaction"] = interaction
            cmd["cmd"] = "sleep 5"
