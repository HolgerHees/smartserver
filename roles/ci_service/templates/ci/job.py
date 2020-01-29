import pexpect 

import subprocess
import pathlib
import glob
import os

from datetime import datetime
from datetime import timedelta

from ci import helper
from ci import virtualbox
from ci import status

max_cleanup_time = 60*10
max_runtime = 60*60*2
max_retries = 2
retry_reasons = [
    b"Network is unreachable"
]
retry_messages = {
    "max_runtime": "Max runtime exceeded",
    "max_starttime": "Max start time exceeded",
    "max_retries": "Max retries exceeded",
    "retry": "Will retry"
}
# 14:17:57.717 fatal: [demo]: FAILED! => {"changed": false, "msg": "Failed to connect to download.nextcloud.com at port 443: [Errno 101] Network is unreachable", "status": -1, "url": "https://download.nextcloud.com/server/releases/nextcloud-18.0.0.zip"}

START_TIME_STR_FORMAT = "%Y.%m.%d_%H.%M.%S"

class LogFile:
    def __init__(self,file):
        self.file = file
        self.hasPrefix =  False
        
    def write(self,text):
        if not self.hasPrefix:
            self.file.write(datetime.now().strftime("%H:%M:%S.%f")[:-3])
            self.file.write(" ")
            self.hasPrefix = True
        
        try:
            text = text.decode("utf-8")
            #self.file.write("XXXX")
        except AttributeError:
            #self.file.write("YYYY")
            pass
          
        pos = text.find("\n")
        #pos = text.find(b"\n")
        if pos != -1:
            self.hasPrefix = False
            if pos == len(text) - 1:
                #self.file.write("AAAA")
                self.file.write(text)
                #self.write(text.decode("utf-8"))
            else:
                (text1,text2) = text.split("\n",1)
                #(text1,text2) = text.split(b"\n",1)
                #self.file.write("BBBB")
                self.file.write(text1)
                #self.file.write(text1.decode("utf-8"))
                self.file.write(u"\n")
                if text2 != "":
                    self.write(text2)
        else:
            self.file.write(text)
            #self.file.write(text.decode("utf-8"))
        
    def flush(self):
        self.file.flush()
      
def modifyStoppedFile(log_dir):
    files = glob.glob("{}*-0-running-*.log".format(log_dir))
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

        finished_log_file = deployment_log_file.replace("-0-running-","-{}-stopped-".format(duration))

        os.rename(deployment_log_file, finished_log_file)
        
        print(u"Logfile '{}' processed.".format(finished_log_file.split('/')[-1]))
        break
      
class Job:
  
    def __init__( self, log_dir, lib_dir, repository_dir, status_file, git_hash ):
        self.log_dir = log_dir
        self.lib_dir = lib_dir
        self.repository_dir = repository_dir
        self.status_file = status_file
        self.git_hash = git_hash

        self.registeredMachines = {}
        self.activeMachine = None
        self.cancelReason = None
        self.start_time = None

    def checkForRetry(self,lines):
        for line in lines:
            for reason in retry_reasons:
                if line.find(reason) != -1:
                    return True
        return False
      
    def searchMachineVID(self,d):
        duration = int(round(datetime.now().timestamp() - self.start_time.timestamp()))
      
        if not self.activeMachine:
            registeredMachines = virtualbox.getRegisteredMachines()
            diff = set(registeredMachines.keys()) - set(self.registeredMachines.keys())
            if len(diff) > 0:
                self.activeMachine = diff.pop()
                status.setVID(self.status_file,self.activeMachine)
            elif duration > 60:
                self.cancelReason = "max_starttime"
                d["child"].close()
                
        if duration > max_runtime:
            self.cancelReason = "max_runtime"
            d["child"].close()
            
        
    def startCheck( self, config_name, os_name, args ):
        argsStr = ""
        if args != None:
            argsStr = u" --args={}".format(args)

        #print("start")
        #output = pexpect.run("sleep 30", timeout=1, cwd=self.repository_dir, withexitstatus=True, events={pexpect.TIMEOUT:self.searchDeploymentVID})
        #print("end")
        #return

        i = 0
        while True:
            self.registeredMachines = virtualbox.getRegisteredMachines()
            self.activeMachine = None
            self.cancelReason = None
          
            self.start_time = datetime.now()
            start_time_str = self.start_time.strftime(START_TIME_STR_FORMAT)

            deployment_log_file = u"{}{}-{}-{}-{}-{}-{}.log".format(self.log_dir,start_time_str,0,"running",config_name,os_name,self.git_hash)
            
            vagrant_path = pathlib.Path(__file__).parent.absolute().as_posix() + "/../vagrant"

            # force VBox folder
            helper.execCommand("VBoxManage setproperty machinefolder {}VirtualMachines".format(self.lib_dir))
            
            env = {"VAGRANT_HOME": self.lib_dir }
            
            # Deployment start
            deploy_exit_status = 1
            deploy_output = ""
            cmd = u"{} --config={} --os={}{} up".format(vagrant_path,config_name,os_name,argsStr)
            #cmd = u"echo '\033[31mtest1\033[0m' && echo '\033[200mtest2' && echo 1 && sleep 5 && echo 2 && sleep 5 && echo 3 2>&1"
            helper.log( u"Deployment for commit '{}' ('{}') started".format(self.git_hash,cmd) )
            with open(deployment_log_file, 'w') as f:
                try:
                    (deploy_output,deploy_exit_status) = pexpect.run(cmd, timeout=1, logfile=LogFile(f), cwd=self.repository_dir, env = env, withexitstatus=True, events={pexpect.TIMEOUT:self.searchMachineVID})
                except ValueError:
                    pass
                  
            # Deployment done
            retry = False
            if deploy_exit_status == 0:
                helper.log( u"Deployment for commit '{}' successful".format(self.git_hash) )
            else:
                if deploy_exit_status != 0:
                    log_lines = deploy_output.split(b"\n")
                    log_lines_to_check = log_lines[-100:] if len(log_lines) > 100 else log_lines
                    i = i + 1
                    # Check if retry is possible
                    if self.checkForRetry(log_lines_to_check):
                        if i < max_retries:
                            self.cancelReason = "retry"
                            retry = True
                        else:
                            self.cancelReason = "max_retries"
                
                reason = u" ({})".format( self.cancelReason ) if self.cancelReason != None else ""
                helper.log( u"Deployment for commit '{}' unsuccessful {}".format(self.git_hash, reason ) )

            # Final logfile preperation
            duration = int(round(datetime.now().timestamp() - self.start_time.timestamp()))
            status_msg = "" 
            with open(deployment_log_file, 'a') as f:
                f.write("\n")
                lf = LogFile(f)
                if deploy_exit_status == 0:
                    lf.write("The command '{}' exited with 0 (successful) after {}.\n".format(cmd,timedelta(seconds=duration)))
                    status_msg = 'success'
                else:
                    if retry:
                        status_msg = 'retry'
                    else:
                        status_msg = 'error'

                    if self.cancelReason != None:
                        lf.write("{}\n".format(retry_messages[self.cancelReason]))
                    
                    lf.write("The command '{}' exited with {} (unsuccessful) after {}.\n".format(cmd,deploy_exit_status,timedelta(seconds=duration)))

            # Rename logfile
            finished_log_file = u"{}{}-{}-{}-{}-{}-{}.log".format(self.log_dir,start_time_str,duration,status_msg,config_name,os_name,self.git_hash)
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

            return deploy_exit_status == 0

        return False 
