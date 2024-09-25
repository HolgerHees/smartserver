import pathlib
import glob
import os
import re
import logging
import threading
import traceback
import urllib

import glob

from datetime import datetime
from datetime import timedelta

from lib import virtualbox
from lib import git

from smartserver.github import GitHub
from smartserver.logfile import LogFile
from smartserver import command
from smartserver import pexpect

max_subject_length = 50
max_cleanup_time = 60*10
#max_runtime = 60*60*2
max_retries = 2
retry_reasons = [
    "Network is unreachable",
    "Failed to download packages: Curl error (7): Couldn't connect to server",
    "Failed to download packages: Curl error (16): Error in the HTTP2 framing layer",
    "Failed to download packages: Status code: 503"
]
# 14:17:57.717 fatal: [demo]: FAILED! => {"changed": false, "msg": "Failed to connect to download.nextcloud.com at port 443: [Errno 101] Network is unreachable", "status": -1, "url": "https://download.nextcloud.com/server/releases/nextcloud-18.0.0.zip"}

START_TIME_STR_FORMAT = "%Y.%m.%d_%H.%M.%S"
 
class DeploymentException(Exception):
    def __init__(self, exitcode, statuscode, details, cmd):
        self.exitcode = exitcode
        self.statuscode = statuscode
        self.details = details
        self.cmd = cmd

    def getExitCode(self):
        return self.exitcode

    def getStatusCode(self):
        return self.statuscode

    def getDetails(self):
        return self.details

    def getCmd(self):
        return self.cmd

class JobRunner:
    def __init__( self, handler, job_state, log_dir, lib_dir, repository_dir, status_file, branch, git_hash, commit ):
        self.is_running = False

        self.handler = handler
        self.job_state = job_state

        self.log_dir = log_dir
        self.lib_dir = lib_dir
        self.repository_dir = repository_dir
        self.status_file = status_file
        self.branch = branch
        self.git_hash = git_hash
        self.commit = commit

        self.registered_machines = {}
        self.max_starttime_exceeded = None
        self.max_starttime_checker = None

        #self.cancel_reason = None
        self.start_time = None

        self.event = threading.Event()
        self.job = None

    def terminate(self):
        if self.is_running:
            self.is_running = False
            if self.job is not None:
                self.job.terminate()

    def startCheck( self, config_name, os_name ):
        self.is_running = True

        #argsStr = ""
        #if args != None:
        #    argsStr = u" --args={}".format(args)

        author = re.sub(r'\W+|\s+', "_", self.commit['author'] );
        subject = re.sub(r'\W+|\s+', "_", self.commit['subject'] );
        if len(subject) > max_subject_length:
            subject = subject[0:max_subject_length]
            pos = subject.rfind("_")
            subject = u"{}_".format(subject[0:pos])

        retry_count = 0
        statuscode = ""
        while self.is_running:
            self.start_time = datetime.now()
            start_time_str = self.start_time.strftime(START_TIME_STR_FORMAT)

            notification_topic = JobRunner.getTopicName(start_time_str, config_name, os_name, self.branch, self.git_hash )

            self.handler.notifyChangedJobRunnerState("running", notification_topic)
            deployment_log_file = JobRunner._getLogFilename(self.log_dir, start_time_str, 0, "running", config_name, os_name, self.branch, self.git_hash, author, subject)

            with LogFile(deployment_log_file, 'w', self.handler.notifyChangedJobRunnerLog, notification_topic) as lf:
                try:
                    vagrant_path = pathlib.Path(__file__).parent.absolute().as_posix() + "/../vagrant"

                    # force VBox folder
                    command.exec( [ "VBoxManage", "setproperty", "machinefolder", "{}VirtualMachines".format(self.lib_dir) ], namespace_pid=command.NAMESPACE_PID_HOST)

                    env = { "VAGRANT_HOME": self.lib_dir, "HOME": os.path.expanduser('~') }

                    # DEPLOYMENT BOX UPDATE
                    # Always test with the latest version
                    logging.info( u"Image check for commit '{}' started".format(self.git_hash) )
                    update_cmd = [ vagrant_path, "--config={}".format(config_name), "--os={}".format(os_name), "box", "update" ]
                    self.job = pexpect.Process(update_cmd, timeout=1800, logfile=lf, cwd=self.repository_dir, env=env, namespace_pid=command.NAMESPACE_PID_HOST)
                    self.job.start()
                    exitcode = self.job.getExitCode()
                    if exitcode != 0:
                        if self.job.isTerminated():
                            raise DeploymentException(exitcode, "stopped", "Terminated", update_cmd)
                        elif self.job.isTimeout():
                            raise DeploymentException(exitcode, "crashed", "Max runtime exceeded", update_cmd)
                        else:
                            raise DeploymentException(exitcode, "failed", None, update_cmd)

                    # DEPLOYMENT RUN
                    deploy_cmd = [ vagrant_path, "--config={}".format(config_name), "--os={}".format(os_name), "up" ]
                    #cmd = u"echo '\033[31mtest1\033[0m' && echo '\033[200mtest2' && echo 1 && sleep 5 && echo 2 && sleep 5 && echo 3 2>&1"
                    logging.info( u"Deployment for commit '{}' ('{}') started".format(self.git_hash,self._fmtCmd(deploy_cmd)) )

                    # all 3 variables will only be used in 'self._watchDeployment'
                    self.registered_machines = virtualbox.getRegisteredMachines()
                    self.max_starttime_exceeded = False
                    self.max_starttime_checker = threading.Timer(5,self._watchDeployment)
                    self.max_starttime_checker.start()

                    self.job = pexpect.Process(deploy_cmd, timeout=7200, logfile=lf, cwd=self.repository_dir, env = env, namespace_pid=command.NAMESPACE_PID_HOST)
                    self.job.start()
                    if self.max_starttime_exceeded:
                        raise DeploymentException(-1, "crashed", "Max start time exceeded", deploy_cmd)
                    exitcode = self.job.getExitCode()
                    if exitcode != 0:
                        if self.job.isTerminated():
                            raise DeploymentException(exitcode, "stopped", "Terminated", deploy_cmd)
                        elif self.job.isTimeout():
                            raise DeploymentException(exitcode, "crashed", "Max runtime exceeded", deploy_cmd)
                        else:
                            output = self.job.getOutput()
                            log_lines = output.split(u"\n")
                            log_lines_to_check = log_lines[-100:] if len(log_lines) > 100 else log_lines
                            if self._checkForRetry(log_lines_to_check):
                                retry_count = retry_count + 1
                                if retry_count > max_retries:
                                    raise DeploymentException(exitcode, "failed", "Max retries exceeded", deploy_cmd)
                                else:
                                    raise DeploymentException(exitcode, "retry", "Will retry", deploy_cmd)
                            else:
                                raise DeploymentException(exitcode, "failed", None, deploy_cmd)
                    else:
                        raise DeploymentException(exitcode, "success", None, deploy_cmd)

                except DeploymentException as e:
                    statuscode = e.getStatusCode()
                    duration = int(round(datetime.now().timestamp() - self.start_time.timestamp()))

                    if e.getDetails() is not None:
                        self._writeWrapppedLog(lf, e.getDetails())

                    if statuscode == "success":
                        msg = "Command '{}' finished successful after {}.".format(self._fmtCmd(e.getCmd()),timedelta(seconds=duration))
                        logging.info(msg)
                        self._writeWrapppedLog(lf, msg)
                    else:
                        msg = "Command '{}' stopped unsuccessful ({}) after {}.".format(self._fmtCmd(e.getCmd()),e.getExitCode(),timedelta(seconds=duration))
                        if self.job.isTerminated():
                            logging.info("{} ({})".format(msg,e.getDetails()))
                        else:
                            logging.error("{} ({})".format(msg,e.getDetails()))
                        self._writeWrapppedLog(lf, msg)

                    # DEPLOYMENT CLEANUP
                    lf.writeRaw("\n")
                    logging.info( u"Cleaning for commit '{}' started".format(self.git_hash) )
                    clean_cmd = [ vagrant_path, "--config={}".format(config_name), "--os={}".format(os_name), "destroy", "--force" ]
                    job = pexpect.Process(clean_cmd, timeout=max_cleanup_time, logfile=lf, cwd=self.repository_dir, env = env, namespace_pid=command.NAMESPACE_PID_HOST)
                    job.start()

                    exitcode = job.getExitCode()
                    if exitcode != 0:
                        if job.isTimeout():
                            msg = u"Cleaning for commit '{}' timed out".format(self.git_hash)
                            logging.error(msg)
                            self._writeWrapppedLog(lf, msg)
                            statuscode = "crashed"
                        else:
                            msg = u"Cleaning for commit '{}' unsuccessful".format(self.git_hash)
                            logging.error(msg)
                            self._writeWrapppedLog(lf, msg)
                            statuscode = "failed"
                    else:
                        self.job_state.setVID(None)
                        self.job_state.save()
                        msg = u"Cleaning for commit '{}' successful".format(self.git_hash)
                        logging.info(msg)
                        self._writeWrapppedLog(lf, msg)

            # Rename logfile
            self.handler.notifyChangedJobRunnerState(statuscode, notification_topic)
            finished_log_file = JobRunner._getLogFilename(self.log_dir, start_time_str, duration, statuscode, config_name, os_name, self.branch, self.git_hash, author, subject)
            os.rename(deployment_log_file, finished_log_file)

            if statuscode == "retry":
                logging.info( u"Retry deployment for commit '{}'".format(self.git_hash) )
                continue

            break

        self.is_running = False

        return statuscode == "success", start_time_str, statuscode

    def _writeWrapppedLog(self, lf, msg):
        lf.writeRaw("\n")
        lf.writeLine(msg)

    def _watchDeployment(self):
        if self.job is None or not self.job.isAlive():
            return

        duration = int(round(datetime.now().timestamp() - self.start_time.timestamp()))

        registered_machines = virtualbox.getRegisteredMachines()
        diff = set(registered_machines.keys()) - set(self.registered_machines.keys())
        if len(diff) > 0:
            self.job_state.setVID(diff.pop())
            self.job_state.save()
        # max 10 min. Long startup time is possible after an image upgrade.
        elif duration > 600:
            self.max_starttime_exceeded = True
            self.job.terminate()
        else:
            self.max_starttime_checker = threading.Timer(5,self._watchDeployment)
            self.max_starttime_checker.start()

    def _checkForRetry(self,lines):
        for line in lines:
            for reason in retry_reasons:
                if line.find(reason) != -1:
                    return True
        return False

    def _fmtCmd(self, cmd):
        return " ".join(cmd)

    @staticmethod
    def _getLogFilename(log_folder, time_str, duration, state, config_name, os_name, branch, git_hash, author, subject ):
        return u"{}{}-{}-{}-{}-{}-{}-{}-{}-{}.log".format(log_folder,time_str,duration, state,config_name,os_name,branch, git_hash,author,subject)

    @staticmethod
    def getTopicName(time_str, config_name, os_name, branch, git_hash ):
        return u"{}-{}-{}-{}-{}".format(time_str,config_name,os_name,branch,git_hash)

    @staticmethod
    def getLogfiles(log_folder, time_str, config_name, os_name, branch, git_hash):
        pattern = JobRunner._getLogFilename(log_folder, time_str, '*', '*', config_name, os_name, branch, git_hash, '*', '*')
        return glob.glob(pattern);

    @staticmethod
    def getLogFileDetails(filename):
        data = os.path.basename(filename).split("-")

        timestamp = datetime.strptime(data[0],"%Y.%m.%d_%H.%M.%S").timestamp()
        return {
            "date": data[0],
            "duration": data[1],
            "state": data[2],
            "config": data[3],
            "deployment": data[4],
            "branch": data[5],
            "git_hash": data[6],
            "author": data[7],
            "subject": data[8][:-4],
            "timestamp": timestamp
        }

class JobExecutor():
    def __init__(self, handler, job_state, config):
        self.handler = handler
        self.job_state = job_state
        self.config = config
        self.current_git_hash = None

        self.is_terminated = False

        self.job_runner = None
        self.executor_thread = None

    def getGitHash(self):
        return self.current_git_hash

    def start(self, current_git_hash, start_os):
        self.is_terminated = False
        self.current_git_hash = current_git_hash
        self.start_os = start_os

        self.executor_thread = threading.Thread(target=self.run)
        self.executor_thread.start()

        self.handler.notifyChangedExecutorRunnerState(True)

    def terminate(self):
        if self.is_terminated:
            return
        self.is_terminated = True
        if self.job_runner != None:
            self.job_runner.terminate()

    def isRunning(self):
        return self.executor_thread is not None

    def isTerminated(self):
        return self.is_terminated

    def cleanLogfile(self):
        logging.info(u"State for commit '{}' changed to '{}'.".format(self.job_state.getGitHash(), self.job_state.getState()))
        files = glob.glob("{}*-{}-{}-{}-{}-*.log".format(self.config.log_dir, self.job_state.getConfig(), self.job_state.getDeployment(), self.config.branch, self.job_state.getGitHash() ) )
        if len(files) > 0:
            logging.info(u"Clean logfiles.")
        self._cleanedFiles(files)

    def cleanLeftoversLogfiles(self):
        files = glob.glob("{}*-[0-9]*-running-*.log".format(self.config.log_dir) )
        if len(files) > 0:
            logging.info(u"Clean leftover logfiles.")
        self._cleanedFiles(files)

    def _cleanedFiles(self, files):
        files.sort(key=os.path.getmtime, reverse=True)
        for deployment_log_file in files:
            filename = deployment_log_file.split('/')[-1]
            parts = filename.split("-")

            start_time = datetime.strptime(parts[0], START_TIME_STR_FORMAT)
            duration = int(round(datetime.now().timestamp() - start_time.timestamp()))

            with LogFile(deployment_log_file, 'a') as lf:
                lf.writeRaw("\n")
                lf.writeLine("Stopped after {}.\n".format(timedelta(seconds=duration)))

            finished_log_file = re.sub("-[0-9]*-(running|failed)-","-{}-crashed-".format(duration),deployment_log_file)

            os.rename(deployment_log_file, finished_log_file)

            logging.info(u"Logfile '{}' processed.".format(finished_log_file.split('/')[-1]))
            break

    def run(self):
        repository_owner = GitHub.getRepositoryOwner(self.config.repository_url)

        try:
            logging.info( u"Check for commit {} started".format(self.current_git_hash))

            self.job_state.setState("running")
            self.job_state.setGitHash(self.current_git_hash)
            self.job_state.save()

            commit = git.getLog(self.config.repository_dir,self.current_git_hash)

            self.job_runner = JobRunner(self.handler, self.job_state, self.config.log_dir, self.config.lib_dir, self.config.repository_dir, self.config.status_file, self.config.branch, self.current_git_hash, commit )

            deployments = self.config.deployments

            if self.config.auth_token != "":
                # get all github states
                deployment_states = GitHub.getStates(repository_owner,self.config.auth_token,self.current_git_hash)

                # mark all non successful jobs as pending and clean others
                _deployments = []
                for deployment in deployments:
                    if self.start_os != "all":
                        if self.start_os == "failed":
                            if deployment['os'] in deployment_states and deployment_states[deployment['os']] == "success":
                                continue
                        elif self.start_os != deployment['os']:
                            continue

                    GitHub.setState(repository_owner,self.config.auth_token,self.current_git_hash,"pending",deployment['os'],"Build pending")
                    _deployments.append(deployment)

                deployments = _deployments

            is_failed_job = False
            for deployment in deployments:
                self.job_state.setConfig(deployment['config'])
                self.job_state.setDeployment(deployment['os'])
                self.job_state.save()

                successful, start_time_str, error_reason = self.job_runner.startCheck( deployment['config'], deployment['os'] )
                if self.is_terminated:
                    if self.config.auth_token != "":
                        GitHub.setState(repository_owner,self.config.auth_token,self.current_git_hash,"failure",deployment['os'],"Build stopped")
                    break

                if not successful:
                    if self.config.auth_token != "":
                        GitHub.setState(repository_owner,self.config.auth_token,self.current_git_hash,"failure",deployment['os'],"Build failed")

                    log_url = "https://{}/ci_service/details/?datetime={}&config={}&os={}&branch={}&hash={}".format(self.config.server_host,start_time_str,deployment['config'],deployment['os'],self.config.branch,self.current_git_hash)
                    log_url = urllib.parse.quote_plus(log_url)

                    body = "Reason: {}".format(error_reason)
                    body += "\n\n"
                    body += "Logs: https://{}/?ref=admin|system|ci|{}".format(self.config.server_host,log_url)
                    body += "\n\n"
                    body += "Commit: https://github.com/{}/commit/{}".format(repository_owner,self.current_git_hash)

                    command.sendEmail("root", "CI Test for '{}' on '{}' not successful".format(deployment['config'],deployment['os']),body, namespace_pid=command.NAMESPACE_PID_HOST)

                    is_failed_job = True
                    break
                else:
                    if self.config.auth_token != "":
                        GitHub.setState(repository_owner,self.config.auth_token,self.current_git_hash,"success",deployment['os'],"Build succeeded")

            if is_failed_job and self.config.auth_token != "":
                GitHub.cancelPendingStates(repository_owner, self.config.auth_token, self.current_git_hash, "Build skipped")

            logging.info( u"Check for commit {} finished".format(self.current_git_hash))
        except Exception as e:
            logging.info( traceback.format_exc(), "err" )
            self.cleanLogfile()

            if self.config.auth_token != "":
                GitHub.cancelPendingStates(repository_owner, self.config.auth_token, self.current_git_hash, "Build crashed")

        self.job_state.setState("finished")
        self.job_state.save()

        self.executor_thread = self.job_runner = None

        self.handler.notifyChangedExecutorRunnerState(False)
