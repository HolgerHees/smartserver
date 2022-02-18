import os
import subprocess
import json
import re
import sys

import glob

from datetime import datetime, timezone
from collections import Counter

from config import config

sys.path.insert(0, "/opt/shared/python")

from smartserver.github import GitHub
from smartserver import command

class DeploymentUpdate:
    def __init__(self,config):
        self.config = config
        
        self.deployment_state = None
        if os.path.isfile(config.deployment_state_file):
            with open(config.deployment_state_file, 'r') as f:
                try:
                    self.deployment_state = json.load(f)
                except JSONDecodeError:
                    pass
      
    def process(self, update_time):
        smartserver_code = None
        smartserver_pull = None
        smartserver_changes = None
        
        if self.deployment_state is None:
            smartserver_code = "missing"
        else:
            # git add files (intent to add)  
            command.exec([ "git", "add", "-N", "*" ], cwd=self.config.deployment_directory )
            result = command.exec([ "git", "diff-index", "--name-status", "origin/master" ], cwd=self.config.deployment_directory )
            uncommitted_changes = result.stdout.decode("utf-8").strip().split("\n")

            deployment_stat = os.stat(self.config.deployment_state_file)
            deployment_mtime = deployment_stat.st_mtime
            
            if len(uncommitted_changes) == 1 and uncommitted_changes[0] == "":
                can_pull = False
                if "github" in self.config.git_remote:
                    result = command.exec([ "git", "ls-remote", self.config.git_remote ], cwd=self.config.deployment_directory )
                    commits = result.stdout.decode("utf-8").strip().split("\n")
                    last_git_hash = commits[0].split("\t")[0]

                    repository_owner = GitHub.getRepositoryOwner(self.config.git_remote)

                    result = GitHub.getStates(repository_owner,last_git_hash)
                    
                    states = Counter(result.values())
                    
                    if "failure" in states:
                        smartserver_code = "failed"
                    elif "pending" in states or "success" not in states:
                        smartserver_code = "pending"
                    else:
                        can_pull = True
                        smartserver_code = "pulled_tested"
                else:
                    can_pull = True
                    smartserver_code = "pulled_untested"
                    
                if can_pull:
                    result = command.exec([ "git", "pull" ], cwd=self.config.deployment_directory )
                    if result.returncode != 0:
                        raise Exception(result.stdout.decode("utf-8"))
                    smartserver_pull = update_time;
            else:
                smartserver_code = "uncommitted"
                
            last_deployment = datetime.fromtimestamp(deployment_mtime, tz=timezone.utc)
            #last_deployment = "2020-01-20 14:02:00.651984+00:00"
            #print( " ".join([ "git", "-C", self.config.deployment_directory, "rev-list", "-1", "--before", str(last_deployment), "origin/master" ]))
            result = command.exec([ "git", "rev-list", "-1", "--before", str(last_deployment), "origin/master" ], cwd=self.config.deployment_directory )
            ref = result.stdout.decode("utf-8").strip()
            
            #print( " ".join([ "git", "-C", self.config.deployment_directory, "diff-index", "--name-status", ref ]))
            result = command.exec([ "git", "diff-index", "--name-status", ref ], cwd=self.config.deployment_directory )
            committed_changes = result.stdout.decode("utf-8").strip().split("\n")

            lines = uncommitted_changes + committed_changes
            lines = [ele.split("\t") for ele in lines]
            
            filtered_lines = {}
            for line in lines:
                if len(line) == 1:
                    continue
                  
                flag, path = line
                
                if flag != "D":
                    file_stat = os.stat("{}/{}".format(self.config.deployment_directory,path))
                    file_mtime = file_stat.st_mtime
                    
                    if file_mtime > deployment_mtime:
                        if path not in filtered_lines or flag == "A":
                            filtered_lines[path] = {"flag": flag, "path": path}
            filtered_lines = dict(sorted(filtered_lines.items()))
                            
            files = glob.glob("{}/**/**/*".format(config.deployment_config_path), recursive = True)
            config_files = {}
            for filename in files:
                file_stat = os.stat(filename)
                if file_stat.st_mtime > deployment_mtime:
                    path = filename[len(config.deployment_directory):]
                    config_files[path] = {"flag": "M", "path": path}

            lines = list(config_files.values()) + list(filtered_lines.values())
            
            smartserver_changes = lines
            
        return smartserver_code, smartserver_pull, smartserver_changes

