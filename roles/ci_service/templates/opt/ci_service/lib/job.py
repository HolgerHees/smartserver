import pexpect 

import subprocess
import pathlib
import glob
import os
import re

import glob

from datetime import datetime
from datetime import timedelta

from lib import helper
from lib import virtualbox
from lib import status
from lib import log

from smartserver.logfile import LogFile

max_subject_length = 50
max_cleanup_time = 60*10
max_runtime = 60*60*2
max_retries = 2
retry_reasons = [
    b"Network is unreachable",
    b"Failed to download packages: Curl error (7): Couldn't connect to server",
    b"Failed to download packages: Curl error (16): Error in the HTTP2 framing layer",
    b"Failed to download packages: Status code: 503"
]
retry_messages = {
    "max_runtime": "Max runtime exceeded",
    "max_starttime": "Max start time exceeded",
    "max_retries": "Max retries exceeded",
    "retry": "Will retry"
}
# 14:17:57.717 fatal: [demo]: FAILED! => {"changed": false, "msg": "Failed to connect to download.nextcloud.com at port 443: [Errno 101] Network is unreachable", "status": -1, "url": "https://download.nextcloud.com/server/releases/nextcloud-18.0.0.zip"}

START_TIME_STR_FORMAT = "%Y.%m.%d_%H.%M.%S"
      
def modifyStoppedFile(log_dir, state_obj, branch):
    files = glob.glob("{}*-{}-{}-{}-{}-*.log".format(log_dir,state_obj['config'],state_obj['deployment'], branch, state_obj['git_hash']))
    files.sort(key=os.path.getmtime, reverse=True)
    for deployment_log_file in files:
        filename = deployment_log_file.split('/')[-1]
        parts = filename.split("-")

        start_time = datetime.strptime(parts[0], START_TIME_STR_FORMAT)
        duration = int(round(datetime.now().timestamp() - start_time.timestamp()))
        
        with open(deployment_log_file, 'a') as f:
            f.write("\n")
            lf = LogFile(f)
            lf.write("Stopped after {}.\n".format(timedelta(seconds=duration)))

        finished_log_file = re.sub("-[0-9]*-(running|failed)-","-{}-stopped-".format(duration),deployment_log_file)

        os.rename(deployment_log_file, finished_log_file)
        
        log.info(u"Logfile '{}' processed.".format(finished_log_file.split('/')[-1]))
        break
 
def getLogFileDetails(filename):
    data = os.path.basename(filename).split("-")
    
    return {
        "date": data[0],
        "duration": data[1],
        "state": data[2],
        "config": data[3],
        "deployment": data[4],
        "branch": data[5],
        "git_hash": data[6],
        "author": data[7],
        "subject": data[8][:-4]
    }
  
def getLogFilename(log_folder, time_str, duration, state, config_name, os_name, branch, git_hash, author, subject ):
    return u"{}{}-{}-{}-{}-{}-{}-{}-{}-{}.log".format(log_folder,time_str,duration, state,config_name,os_name,branch, git_hash,author,subject)
  
class Job:
  
    def __init__( self, log_dir, lib_dir, repository_dir, status_file, branch, git_hash, commit ):
        self.log_dir = log_dir
        self.lib_dir = lib_dir
        self.repository_dir = repository_dir
        self.status_file = status_file
        self.branch = branch
        self.git_hash = git_hash
        self.commit = commit

        self.registered_machines = {}
        self.active_machine = None
        self.cancel_reason = None
        self.start_time = None
        self.start_time_str = None

    def checkForRetry(self,lines):
        for line in lines:
            for reason in retry_reasons:
                if line.find(reason) != -1:
                    return True
        return False
      
    def searchMachineVID(self,d):
        duration = int(round(datetime.now().timestamp() - self.start_time.timestamp()))
      
        if not self.active_machine:
            registered_machines = virtualbox.getRegisteredMachines()
            diff = set(registered_machines.keys()) - set(self.registered_machines.keys())
            if len(diff) > 0:
                self.active_machine = diff.pop()
                status.setVID(self.status_file,self.active_machine)
            # max 3 min. Long startup time is possible after an image upgrade.
            elif duration > 180:
                self.cancel_reason = "max_starttime"
                d["child"].close()
                
        if duration > max_runtime:
            self.cancel_reason = "max_runtime"
            d["child"].close()
            
        
    def startCheck( self, config_name, os_name, args ):
        argsStr = ""
        if args != None:
            argsStr = u" --args={}".format(args)

        #output = pexpect.run("sleep 30", timeout=1, cwd=self.repository_dir, withexitstatus=True, events={pexpect.TIMEOUT:self.searchDeploymentVID})
        #return
        
        author = re.sub('\\W+|\\s+', "_", self.commit['author'] );
        subject = re.sub('\\W+|\\s+', "_", self.commit['subject'] );
        if len(subject) > max_subject_length:
            subject = subject[0:max_subject_length]
            pos = subject.rfind("_")
            subject = u"{}_".format(subject[0:pos])

        i = 0
        while True:
            self.registered_machines = {}
            self.active_machine = None
            self.cancel_reason = None
            self.deploy_exit_status = 1
          
            self.start_time = datetime.now()
            self.start_time_str = self.start_time.strftime(START_TIME_STR_FORMAT)

            deployment_log_file = getLogFilename(self.log_dir,self.start_time_str,0,"running",config_name,os_name,self.branch,self.git_hash,author,subject)
            
            vagrant_path = pathlib.Path(__file__).parent.absolute().as_posix() + "/../vagrant"

            # force VBox folder
            helper.execCommand("VBoxManage setproperty machinefolder {}VirtualMachines".format(self.lib_dir))
            
            env = {"VAGRANT_HOME": self.lib_dir }

            with open(deployment_log_file, 'w') as f:
                try:
                    # Always test with the latest version
                    helper.log(u"Check for new images")
                    update_cmd = u"{} --config={} --os={} box update".format(vagrant_path,config_name,os_name)
                    (update_output,update_exit_status) = pexpect.run(update_cmd, timeout=1800, logfile=LogFile(f), cwd=self.repository_dir, env = env, withexitstatus=True)
                except ValueError:
                    #helper.log( update_output )
                    #helper.log( traceback.format_exc(), "err" )
                    pass
            
            self.registered_machines = virtualbox.getRegisteredMachines()

            #helper.log( u"{}".format("VAGRANT_HOME={}".format(self.lib_dir)))
            #helper.log( u"{}".format(update_exit_status) )
            #helper.log( u"{}".format(update_output) )

            # Deployment start
            deploy_output = b""
            cmd = u"{} --config={} --os={}{} up".format(vagrant_path,config_name,os_name,argsStr)
            #cmd = u"echo '\033[31mtest1\033[0m' && echo '\033[200mtest2' && echo 1 && sleep 5 && echo 2 && sleep 5 && echo 3 2>&1"
            helper.log( u"Deployment for commit '{}' ('{}') started".format(self.git_hash,cmd) )
            with open(deployment_log_file, 'a') as f:
                try:
                    (deploy_output,self.deploy_exit_status) = pexpect.run(cmd, timeout=1, logfile=LogFile(f), cwd=self.repository_dir, env = env, withexitstatus=True, events={pexpect.TIMEOUT:self.searchMachineVID})
                except ValueError:
                    #helper.log( deploy_output )
                    #helper.log( traceback.format_exc(), "err" )
                    pass
                    
            # Deployment done
            retry = False
            if self.deploy_exit_status == 0:
                helper.log( u"Deployment for commit '{}' successful".format(self.git_hash) )
                self.cancel_reason = None
            else:
                if self.cancel_reason == None:
                    log_lines = deploy_output.split(b"\n")
                    
                    log_lines_to_check = log_lines[-100:] if len(log_lines) > 100 else log_lines
                    i = i + 1
                    # Check if retry is possible
                    if self.checkForRetry(log_lines_to_check):
                        if i < max_retries:
                            self.cancel_reason = "retry"
                            retry = True
                        else:
                            self.cancel_reason = "max_retries"

                reason = u" ({})".format( self.cancel_reason ) if self.cancel_reason != None else ""
                helper.log( u"Deployment for commit '{}' unsuccessful {}".format(self.git_hash, reason ) )                    

            # Final logfile preperation
            duration = int(round(datetime.now().timestamp() - self.start_time.timestamp()))
            status_msg = "" 
            with open(deployment_log_file, 'a') as f:
                f.write("\n")
                lf = LogFile(f)
                if self.deploy_exit_status == 0:
                    lf.write("The command '{}' exited with 0 (successful) after {}.\n".format(cmd,timedelta(seconds=duration)))
                    status_msg = 'success'
                else:
                    if retry:
                        status_msg = 'retry'
                    else:
                        status_msg = 'failed'

                    if self.cancel_reason != None:
                        lf.write("{}\n".format(retry_messages[self.cancel_reason]))
                    
                    lf.write("The command '{}' exited with {} (unsuccessful) after {}.\n".format(cmd,self.deploy_exit_status,timedelta(seconds=duration)))

            # Rename logfile
            finished_log_file = getLogFilename(self.log_dir,self.start_time_str,duration,status_msg,config_name,os_name,self.branch,self.git_hash,author,subject)
            os.rename(deployment_log_file, finished_log_file)

            # Cleanup start
            helper.log( u"Cleaning for commit '{}' started".format(self.git_hash) )
            cmd = u"{} --config={} --os={} destroy --force".format(vagrant_path,config_name,os_name)
            (destroy_output,destroy_exit_status) = pexpect.run( cmd, timeout=max_cleanup_time, cwd=self.repository_dir, env = env, withexitstatus=True )
            status.setVID(self.status_file,None)
            
            # Cleanup done
            if destroy_exit_status == 0:
                helper.log( u"Cleaning for commit '{}' successful".format(self.git_hash) )
            else:
                helper.log( u"Cleaning for commit '{}' unsuccessful".format(self.git_hash) )

            if retry:
                helper.log( u"Retry deployment for commit '{}'".format(self.git_hash) )
                continue

            break

        return self.deploy_exit_status == 0, self.start_time_str, self.cancel_reason if self.cancel_reason != None else "deployment"
