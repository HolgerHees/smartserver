import sys
import os
import signal

from time import time

from ci import helper
from ci import job
from ci import status
from ci import virtualbox

def getPid():
    #vagrantPID = helper.getPid(1,"vagrant")
    pid = helper.getPid(1,"/usr/bin/python3 \\./ci_service")
    return pid if pid != "" else None

def stopRunningJob(status_file,log_dir):
    cleaned = False
    pid = getPid()
    if pid != None:
        print(u"Job with pid '{}' killed.".format(pid))
        os.kill(int(pid), signal.SIGTERM)
        cleaned = True

        # Prepare file
        job.modifyStoppedFile(log_dir)
    
    status_obj = status.getStatus(status_file)
    
    if status_obj["vid"] != None:
        if virtualbox.destroyMachine(status_obj["vid"]):
            cleaned = True
        else:
            print(u"Cleaning status file.")
        status.setVID(status_file,None)

    if cleaned:
        if status_obj != None:
            status.setStatus(status_file,u"cleaned")
    else:
        print(u"Nothing stopped.")

def checkRunningJob(status_file):
    status_obj = status.getStatus(status_file)
    if status_obj:
        # check 4 hours
        if time() - status_obj["last_modified"] > 14000:
            if status_obj["status"] == "running":
                status.setStatus(status_file,u"crashed")
                print(u"Check for commit '{}' is running too long. Marked as 'crashed' now. Maybe it is stucked and you should try to cleanup manually.".format(status_obj["git_hash"]), file=sys.stderr )
                # check for frozen processes
                exit(1)
            elif status_obj["status"] == "crashed":
                print(u"Skipped check. Previous check for commit '{}' was crashing.".format(status_obj["git_hash"]))
                exit(0)
        else:
            if status_obj["status"] == "running":
                pid = getPid()
                if pid != None:
                    print(u"Check for commit '{}' is still running with pid '{}'.".format(status_obj["git_hash"],pid))
                    exit(0)
                else:
                    status.setStatus(status_file,u"crashed")
                    print(u"Check for commit '{}' marked as 'running', but pid was not found. Marked as 'crashed' now.".format(status_obj["git_hash"]), file=sys.stderr)
                    exit(1)

        return status_obj["git_hash"]
    return ""
