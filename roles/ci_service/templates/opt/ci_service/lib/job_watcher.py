import threading
import glob
import os
from pathlib import Path
from datetime import datetime, timedelta
import logging

from smartserver.github import GitHub

from lib import service
from lib import job_runner
from lib import git

from lib import status


class JobWatcher():
    def __init__(self, handler, config):
        self.is_running = False
        self.state = None

        self.handler = handler
        self.config = config

        self.all_jobs = []
        self.running_jobs = {}
        self.last_none_running_job = None

        self.last_mtime = 0
        self.initJobs()
        
        self.job_activity_pid = None
        
        self.repository_owner = GitHub.getRepositoryOwner(self.config.repository_url)

    def changedJobs(self, event):
        #logging.info("Job changed")
        self.initJobs()
        self.handler.notifyChangedJobWatcherData()

    def initJobs(self):
        jobs = glob.glob(u"{}*.log".format(self.config.log_dir))
        all_jobs = []
        running_jobs = {}
        last_none_running_job = None
        for name in jobs:
            details = job_runner.JobRunner.getLogFileDetails(name)
            subject = details["subject"]
            if subject[-1:] == "_":
                subject = u"{}...".format(subject[:-1])
            subject = subject.replace("_", " ")
            timestamp = details["timestamp"]
            all_jobs.append({
                "author": details["author"].replace("_", " "),
                "branch": details["branch"],
                "config": details["config"],
                "deployment": details["deployment"],
                "duration": details["duration"],
                "git_hash": details["git_hash"],
                "state": details["state"],
                "subject": subject,
                "date": details["date"],
                "timestamp": timestamp
            })
            if details["state"] == "running":
                running_jobs[name] = details
            elif details["state"] != "stopped" and ( last_none_running_job is None or last_none_running_job[0] < timestamp ):
                last_none_running_job = [ timestamp, details ]

        self.all_jobs = all_jobs
        self.running_jobs = running_jobs
        self.last_none_running_job = last_none_running_job
                        
    def lastJobFailed(self):
        return self.last_none_running_job is not None and self.last_none_running_job[1]["state"] in ["failed", "crashed"]

    def getJobs(self):
        return self.all_jobs

class NetworkException(Exception):
    pass
