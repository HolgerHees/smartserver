import os
import subprocess
import json
import re

from datetime import datetime, timezone


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
      
    def process(self):
        smartserver_code = None
        smartserver_pull = None
        smartserver_changes = None
        
        if self.deployment_state is None:
            smartserver_code = "missing"
        else:
            # git add files (intent to add)  
            subprocess.run([ "git", "-C", self.config.git_directory, "add", "-N", "*" ], check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=None )
            result = subprocess.run([ "git", "-C", self.config.git_directory, "diff-index", "--name-status", "origin/master" ], check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=None )
            uncommitted_changes = result.stdout.decode("utf-8").strip().split("\n")

            deployment_stat = os.stat(self.config.deployment_state_file)
            deployment_mtime = deployment_stat.st_mtime

            if len(uncommitted_changes) == 1 and uncommitted_changes[0] == "":
                can_pull = False
                if "github" in self.config.git_remote:
                    result = subprocess.run([ "git", "ls-remote", self.config.git_remote ], check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=None )
                    commits = result.stdout.decode("utf-8").strip().split("\n")
                    last_git_hash = commits[0].split("\t")[0]

                    repository_owner = self.config.git_remote.replace("https://github.com/","")
                    repository_owner = repository_owner.replace(".git","")
                    statusUrl = "https://api.github.com/repos/{}/statuses/{}".format(repository_owner,last_git_hash)

                    result = subprocess.run([ "/usr/bin/wget", "-qO", "-", statusUrl ], check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=None )
                    result = result.stdout.decode("utf-8").strip()
                    
                    json_result = json.loads(result)

                    build_pending_states = {}
                    build_failed_states = {}
                    build_success_states = {}
                    for build_state in json_result:
                        if build_state["state"] == "success":
                            build_success_states[build_state["context"]] = True 
                        elif build_state["state"] == "failure":
                            build_failed_states[build_state["context"]] = False 
                        elif build_state["state"] == "pending":
                            build_pending_states[build_state["context"]] = None 

                    if len(build_failed_states) > 0:
                        smartserver_code = "failed"
                    elif len(build_success_states) < 3:
                        smartserver_code = "pending"
                    else:
                        can_pull = True
                        smartserver_code = "pulled_tested"
                else:
                    can_pull = True
                    smartserver_code = "pulled_untested"
                    
                if can_pull:
                    result = subprocess.run([ "git", "pull" ], check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=None )
                    smartserver_pull = update_time;
            else:
                smartserver_code = "uncommitted"
                
            last_deployment = datetime.fromtimestamp(deployment_mtime, tz=timezone.utc)
            #last_deployment = "2020-01-20 14:02:00.651984+00:00"
            #print( " ".join([ "git", "-C", self.config.git_directory, "rev-list", "-1", "--before", str(last_deployment), "origin/master" ]))
            result = subprocess.run([ "git", "-C", self.config.git_directory, "rev-list", "-1", "--before", str(last_deployment), "origin/master" ], check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=None )
            ref = result.stdout.decode("utf-8").strip()
            
            #print( " ".join([ "git", "-C", self.config.git_directory, "diff-index", "--name-status", ref ]))
            result = subprocess.run([ "git", "-C", self.config.git_directory, "diff-index", "--name-status", ref ], check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=None )
            committed_changes = result.stdout.decode("utf-8").strip().split("\n")

            lines = uncommitted_changes + committed_changes
            lines = [ele.split("\t") for ele in lines]
            
            filtered_lines = {}
            for line in lines:
                if len(line) == 1:
                    continue
                  
                flag, path = line
                
                if flag != "D":
                    file_stat = os.stat("{}/{}".format(self.config.git_directory,path))
                    file_mtime = file_stat.st_mtime
                    
                    if file_mtime > deployment_mtime:
                        if path not in filtered_lines or flag == "A":
                            filtered_lines[path] = {"flag": flag, "path": path}
                            
            filtered_values = filtered_lines.values()
            lines = list(filtered_values)
            
            smartserver_changes = lines
            
        return smartserver_code, smartserver_pull, smartserver_changes

