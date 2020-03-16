import pexpect 

import subprocess
import pathlib
import glob
import os
import re

from datetime import datetime
from datetime import timedelta

from ci import helper
from ci import virtualbox
from ci import status
from ci import log

max_subject_length = 50
max_cleanup_time = 60*10
max_runtime = 60*60*2
max_retries = 2
retry_reasons = [
    b"Network is unreachable",
    b"Failed to download packages: Curl error (7): Couldn't connect to server",
    b"Failed to download packages: Curl error (16): Error in the HTTP2 framing layer"
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
        self.new_line =  False
        self.active_colors = []
        self.cleaned_color = False
        
    def write(self,text):
        try:
            text = text.decode("utf-8")
        except AttributeError:
            pass

        # clean linefeeds
        text = text.replace("\r\n","\n")

        # handle carriage return
        text = text.replace("\r\x1b[K","\n")
        text = text.replace("\r","\n")

        lines = text.split("\n")
        
        for i in range(len(lines)):
            line = lines[i]

            if i > 0:
                # add the date on any line which was empty before
                if self.new_line == True:
                    self.file.write("{} ".format(datetime.now().strftime("%H:%M:%S.%f")[:-3]))
                # cleaned any color, if it was not cleaned before
                if len(self.active_colors) > 0 and self.cleaned_color == False:
                    self.file.write("\x1b[0m")
                # start new line
                self.file.write("\n")
                self.new_line =  True
            
            # remove any clean color statement from the beginning of a line
            while len(line) >= 4:
                prefix = line[0:4]
                if prefix=="\x1b[0m":
                    #self.file.write(prefix)
                    line = line[4:]
                    self.active_colors = []
                else:
                    break
                        
            if line != "":
                if self.new_line == True:
                    # add the date to any new non empty line
                    self.file.write("{} ".format(datetime.now().strftime("%H:%M:%S.%f")[:-3]))
                    # reinitialize registered colors
                    if len(self.active_colors) > 0:
                        for color in self.active_colors:
                            self.file.write(color)
                    self.new_line =  False

                # check if there are registered colors, is needed for the later 'cleanup' ending check
                had_colors = len(self.active_colors) > 0
                
                # find all color definitions
                colors = re.findall(r"(\x1b\[([0-9]+[;0-9]*)m)",line)
                for color in colors:
                    # handle clean color
                    if color[1] == "0":
                        self.active_colors = []
                    # else register color
                    else:
                        self.active_colors.append(color[0])
                        had_colors = True

                if len(line) >= 4:
                    # is the line ending with a cleanup?
                    if line[-4:] == "\x1b[0m":
                        # keep cleanup, because we had colors
                        if had_colors:
                            self.cleaned_color = True
                        # remove cleanup, because there was no used color
                        else:
                            line = line[0:-4]
                            self.cleaned_color = False
                    # no cleanup at the end
                    else:
                        self.cleaned_color = False

                self.file.write(u"{}".format(line))

            '''if i > 0:
                self.new_line =  True
                self.file.write("\n")
            
            if len(line) >= 4:
                prefix = line[0:4]
                if prefix=="\x1b[0m":
                    self.file.write(prefix)
                    line = line[4:]
                    self.active_colors = []
                        
            if line != "":
                if self.new_line == True:
                    if len(self.active_colors) > 0:
                        self.file.write("\x1b[0m")
                    self.file.write("{} ".format(datetime.now().strftime("%H:%M:%S.%f")[:-3]))
                    if len(self.active_colors) > 0:
                        for color in self.active_colors:
                            self.file.write(color)
                    #self.file.write("{}|{} ".format(len(self.active_colors),datetime.now().strftime("%H:%M:%S.%f")[:-3]))
                    self.new_line =  False

                self.file.write(u"{}".format(line))

                colors = re.findall(r"(\x1b\[([0-9]+[;0-9]*)m)",line)
                for color in colors:
                    if color[1] == "0":
                        self.active_colors = []
                    else:
                        self.active_colors.append(color[0])'''
        
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
        
        log.info(u"Logfile '{}' processed.".format(finished_log_file.split('/')[-1]))
        break

def getLastValidState(log_dir,state_obj,branch):
    files = glob.glob("{}*-{}-{}-{}-*.log".format(log_dir,state_obj['deployment'], branch, state_obj['git_hash']))
    files.sort(key=os.path.getmtime, reverse=True)
    for deployment_log_file in files:
        if deployment_log_file.find("-success-"):
            return u"success"
        elif deployment_log_file.find("-failure-"):
            return u"failure"
    return None
  
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
            elif duration > 60:
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
            self.registered_machines = virtualbox.getRegisteredMachines()
            self.active_machine = None
            self.cancel_reason = None
            self.deploy_exit_status = 1
          
            self.start_time = datetime.now()
            self.start_time_str = self.start_time.strftime(START_TIME_STR_FORMAT)

            deployment_log_file = u"{}{}-{}-{}-{}-{}-{}-{}-{}-{}.log".format(self.log_dir,self.start_time_str,0,"running",config_name,os_name,self.branch,self.git_hash,author,subject)
            
            vagrant_path = pathlib.Path(__file__).parent.absolute().as_posix() + "/../vagrant"

            # force VBox folder
            helper.execCommand("VBoxManage setproperty machinefolder {}VirtualMachines".format(self.lib_dir))
            
            env = {"VAGRANT_HOME": self.lib_dir }
            
            # Deployment start
            deploy_output = ""
            cmd = u"{} --config={} --os={}{} up".format(vagrant_path,config_name,os_name,argsStr)
            #cmd = u"echo '\033[31mtest1\033[0m' && echo '\033[200mtest2' && echo 1 && sleep 5 && echo 2 && sleep 5 && echo 3 2>&1"
            helper.log( u"Deployment for commit '{}' ('{}') started".format(self.git_hash,cmd) )
            with open(deployment_log_file, 'w') as f:
                try:
                    (deploy_output,self.deploy_exit_status) = pexpect.run(cmd, timeout=1, logfile=LogFile(f), cwd=self.repository_dir, env = env, withexitstatus=True, events={pexpect.TIMEOUT:self.searchMachineVID})
                except ValueError:
                    pass
                    
            # Deployment done
            retry = False
            if self.deploy_exit_status == 0:
                helper.log( u"Deployment for commit '{}' successful".format(self.git_hash) )
                self.cancel_reason = None
            else:
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
                else:
                    self.cancel_reason = None

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
            finished_log_file = u"{}{}-{}-{}-{}-{}-{}-{}-{}-{}.log".format(self.log_dir,self.start_time_str,duration,status_msg,config_name,os_name,self.branch,self.git_hash,author,subject)
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
