import os
import subprocess
import json
import re

import glob

from datetime import datetime, timezone
from collections import Counter

from config import config

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
      
    def filterPath( self, flag, path, deployment_mtime, filtered_lines ):
        if flag != "D":
            file_stat = os.stat("{}/{}".format(self.config.deployment_directory,path))
            file_mtime = file_stat.st_mtime
            
            if file_mtime > deployment_mtime:
                if path not in filtered_lines or flag == "A":
                    filtered_lines[path] = {"flag": flag, "path": path}
                    return True
        return False

    def process(self, update_time):
        smartserver_code = None
        smartserver_pull = None
        smartserver_changes = None
        
        if self.deployment_state is None:
            smartserver_code = "missing_state"
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
                        smartserver_code = "ci_failed"
                    elif "pending" in states:
                        smartserver_code = "ci_pending"
                    elif "success" not in states:
                        smartserver_code = "ci_missing"
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
                smartserver_code = "uncommitted_changes"
                
            last_deployment = datetime.fromtimestamp(deployment_mtime, tz=timezone.utc)
            last_deployment = datetime.strptime("2022-03-13 00:00:00 +0100","%Y-%m-%d %H:%M:%S %z")
            
            #print( " ".join([ "git", "-C", self.config.deployment_directory, "rev-list", "-1", "--before", str(last_deployment), "origin/master" ]))
            result = command.exec([ "git", "rev-list", "-1", "--before", str(last_deployment), "origin/master" ], cwd=self.config.deployment_directory )
            ref = result.stdout.decode("utf-8").strip()
            
            #print( " ".join([ "git", "-C", self.config.deployment_directory, "diff-index", "--name-status", ref ]))
            #result = command.exec([ "git", "diff-index", "--name-status", ref ], cwd=self.config.deployment_directory )
            #committed_changes = result.stdout.decode("utf-8").strip().split("\n")

            # prepare commit messages
            result = command.exec([ "git", "log", "--name-status", "--date=iso", str(ref) +  "..origin/master" ], cwd=self.config.deployment_directory )
            committed_changes = result.stdout.decode("utf-8").strip().split("\n")
            
            commits = {}
            current_commit = None
            current_date = None
            current_message = []
            current_files = []
            for line in committed_changes:
                if len(line) == 0:
                    continue

                if len(line) > 6 and line[:6] == "commit":
                    if current_commit is not None:
                        commits[current_commit] = {"date": current_date, "messages": current_message, "files": current_files }
                    current_commit = line[6:].strip().split(" ",1)[0]
                    current_date = None
                    current_message = []
                    current_files = []
                    continue
                elif current_commit is None:
                    continue
                
                if len(line) > 5 and line[:5] == "Date:":
                    current_date = line[5:].strip()
                    continue
                elif current_date is None:
                    continue
                                
                if line[0] == " ":
                    current_message.append(line.strip())
                    continue

                current_files.append( line.split("\t") )
                
            #print(commits)
            
            filtered_lines = {}
            filtered_commit_messages = []
            for commit in commits:
                for file in commits[commit]["files"]:
                    flag, path = file
                    
                    success = self.filterPath( flag, path, deployment_mtime, filtered_lines )
                    if success:
                        date = "{}T{}.000000{}:{}".format(commits[commit]["date"][:10],commits[commit]["date"][11:19],commits[commit]["date"][20:23],commits[commit]["date"][23:])
                        filtered_commit_messages.append({"date": date, "message": "\n".join(commits[commit]["messages"]) })

            #print(commits)
            #print(filtered_commit_messages)
            #print(filtered_lines)
            #print(last_deployment)
            #print(commit_lines)
            #print(committed_changes)

            lines = [ele.split("\t") for ele in uncommitted_changes]
            for line in lines:
                if len(line) == 1:
                    continue
                flag, path = line
                self.filterPath( flag, path, deployment_mtime, filtered_lines )

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
            
        return smartserver_code, smartserver_pull, smartserver_changes, filtered_commit_messages
