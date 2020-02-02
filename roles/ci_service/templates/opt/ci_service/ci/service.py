import sys
import os
import signal

from time import time

from ci import helper
from ci import job
from ci import status
from ci import virtualbox
from ci import log

def getPid():
    #vagrantPID = helper.getPid(1,"vagrant")
    pid = helper.getPid(1,"/usr/bin/python3.*ci_service")
    return pid if pid != "" else None

skipped_names = [
    "grep",
    "ci_service status",
    "VBoxXPCOMIPCD",
    "VBoxSVC"
]
def checkIfSkippedName(line):
    for name in skipped_names:
        if line.find(name) != -1 or line == "":
            return True
  
def formatProcesses(lines,processes):
    for line in lines:
        line = line.strip()
        if checkIfSkippedName(line):
            continue
        processes.append(u"  {}".format(line))
  
def showRunningJobs():
    pid = getPid()
    if pid != None:
        log.info(u"Main process is running with pid '{}'.".format(pid))
    else:
        log.info(u"Main process is not running.")
    
    processes = []
    
    ci_result = helper.execCommand("ps -alx | grep ci_service")
    ci_lines = ci_result.stdout.decode("utf-8").split(u"\n")
    formatProcesses(ci_lines,processes)
    
    vm_result = helper.execCommand("ps -alx | grep virtualbox")
    vm_lines = vm_result.stdout.decode("utf-8").split(u"\n")
    formatProcesses(vm_lines,processes)
    
    if len(processes) > 0:
        log.info(u"Following sub processes are running.")
        log.info(u"\n".join(processes))
    else:
        log.info(u"No sub processes are running.")

    virtualbox.checkMachines(True)
      
def cleanRunningJobs(vid):
    if vid == "all":
        machines = virtualbox.getRegisteredMachines()
        for vid in machines.keys():
            virtualbox.destroyMachine(vid)
    else:
        virtualbox.destroyMachine(vid)

def stopRunningJob(status_file,log_dir):
    cleaned = False
    pid = getPid()
    if pid != None:
        log.info(u"Job with pid '{}' killed.".format(pid))
        os.kill(int(pid), signal.SIGTERM)
        cleaned = True

        # Prepare file
        job.modifyStoppedFile(log_dir)
    
    state_obj = status.getState(status_file)
    
    if state_obj["vid"] != None:
        if virtualbox.destroyMachine(state_obj["vid"]):
            cleaned = True
        else:
            log.info(u"Cleaning status file.")
        status.setVID(status_file,None)
        
    virtualbox.checkMachines(False)

    if cleaned:
        if state_obj != None:
            status.setState(status_file,u"cleaned")
            return status.getState(status_file);
    else:
        log.info(u"Nothing stopped.")
        
    return None

def checkRunningJob(status_file):
    state_obj = status.getState(status_file)
    if state_obj:
        # check 4 hours
        if time() - state_obj["last_modified"] > 14000:
            if state_obj["status"] == "running":
                status.setState(status_file,u"crashed")
                log.error(u"Check for commit '{}' is running too long. Marked as 'crashed' now. Maybe it is stucked and you should try to cleanup manually.".format(state_obj["git_hash"]), file=sys.stderr )
                # check for frozen processes
                exit(1)
            elif state_obj["status"] == "crashed":
                log.info(u"Skipped check. Previous check for commit '{}' was crashing.".format(state_obj["git_hash"]))
                exit(0)
        else:
            if state_obj["status"] == "running":
                pid = getPid()
                if pid != None:
                    log.info(u"Check for commit '{}' is still running with pid '{}'.".format(state_obj["git_hash"],pid))
                    exit(0)
                else:
                    status.setState(status_file,u"crashed")
                    log.error(u"Check for commit '{}' marked as 'running', but pid was not found. Marked as 'crashed' now.".format(state_obj["git_hash"]), file=sys.stderr)
                    exit(1)

        return state_obj["git_hash"]
    return ""
