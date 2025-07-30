import os
import subprocess
import json
import re

import glob

from datetime import datetime, timezone
from collections import Counter

from smartserver.github import GitHub
from smartserver import command

class DeploymentUpdate:
    def __init__(self, config):
        self.config = config
        
        self.deployment_state = None
        if os.path.isfile(self.config.deployment_state_file):
            with open(config.deployment_state_file, 'r') as f:
                try:
                    self.deployment_state = json.load(f)
                except JSONDecodeError:
                    pass
      
    def filterPath( self, flag, path, max_mtime ):
        if flag != "D":
            file_stat = os.stat("{}/{}".format(self.config.deployment_directory,path))
            file_mtime = file_stat.st_mtime
            
            if file_mtime > max_mtime:
                return True
        return False
    
    def prepareCommit(self,current_date,current_commit,current_messages,current_files,repository_owner):
        current_date = "{}T{}.000000{}:{}".format(current_date[:10],current_date[11:19],current_date[20:23],current_date[23:])
        url = "https://github.com/{}/commit/{}".format(repository_owner,current_commit) if repository_owner is not None else None
        return {"date": current_date, "message": "\n".join(current_messages), "files": current_files, "url": url }

    def process(self):
        smartserver_code = None
        smartserver_pull = None
        smartserver_changes = None
        
        if self.deployment_state is None:
            smartserver_code = "missing_state"
        else:
            # git add files (intent to add)  
            command.exec([ "git", "add", "-N", "*" ], cwd=self.config.deployment_directory )
            #result = command.exec([ "git", "diff-index", "--name-status", "origin/master" ], cwd=self.config.deployment_directory )
            result = command.exec([ "git", "status", "--porcelain" ], cwd=self.config.deployment_directory )
            uncommitted_changes = result.stdout.decode("utf-8").strip().split("\n")

            last_deployment_state = {}
            if os.path.isfile(self.config.deployment_state_file):
                with open(self.config.deployment_state_file, 'r') as f:
                    last_deployment_state = json.load(f)
            
            repository_owner = GitHub.getRepositoryOwner(self.config.git_remote) if "github" in self.config.git_remote else None

            if len(uncommitted_changes) == 1 and uncommitted_changes[0] == "":
                uncommitted_changes = []

                can_pull = False
                if "github" in self.config.git_remote:
                    result = command.exec([ "git", "ls-remote", self.config.git_remote ], cwd=self.config.deployment_directory )
                    commits = result.stdout.decode("utf-8").strip().split("\n")
                    last_git_hash = commits[0].split("\t")[0]

                    result = GitHub.getStates(repository_owner, self.config.global_config["github_auth_token"], last_git_hash)
                    
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
            else:
                smartserver_code = "uncommitted_changes"
                
            _name = ".git/FETCH_HEAD" if os.path.exists(self.config.deployment_directory + "/.git/FETCH_HEAD") else ".git/HEAD"
            result = command.exec([ "stat", "-c", "%y", _name ], cwd=self.config.deployment_directory )
            last_git_pull = result.stdout.decode("utf-8").strip()
            smartserver_pull = "{}T{}{}:{}".format(last_git_pull[0:10],last_git_pull[11:26],last_git_pull[-5:-2],last_git_pull[-2:])

            last_deployment_as_string = "{}{}".format(last_deployment_state["deployment_date"][0:-3],last_deployment_state["deployment_date"][-2:])
            last_deployment = datetime.strptime(last_deployment_as_string,"%Y-%m-%dT%H:%M:%S.%f%z")
                        
            #print( " ".join([ "git", "-C", self.config.deployment_directory, "rev-list", "-1", "--before", str(last_deployment), "origin/master" ]))
            #result = command.exec([ "git", "rev-list", "-1", "--before", str(last_deployed_git), "HEAD" ], cwd=self.config.deployment_directory )
            #ref = result.stdout.decode("utf-8").strip()
            
            #print( " ".join([ "git", "-C", self.config.deployment_directory, "diff-index", "--name-status", ref ]))
            #result = command.exec([ "git", "diff-index", "--name-status", ref ], cwd=self.config.deployment_directory )
            #committed_changes = result.stdout.decode("utf-8").strip().split("\n")

            # prepare commit messages
            result = command.exec([ "git", "log", "--name-status", "--date=iso", last_deployment_state["git_hash"] +  "..HEAD" ], cwd=self.config.deployment_directory )
            committed_changes = result.stdout.decode("utf-8").strip().split("\n")
            #print(committed_changes)
            
            commits = {}
            current_commit = None
            current_date = None
            current_messages = []
            current_files = []
            for line in committed_changes:
                if len(line) == 0:
                    continue

                if len(line) > 6 and line[:6] == "commit":
                    if current_commit is not None:
                        commits[current_commit] = self.prepareCommit(current_date,current_commit,current_messages,current_files,repository_owner)
                    current_commit = line[6:].strip().split(" ",1)[0]
                    current_date = None
                    current_messages = []
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
                    current_messages.append(line.strip())
                    continue

                current_files.append( line.split("\t") )
                
            if current_commit is not None:
                commits[current_commit] = self.prepareCommit(current_date,current_commit,current_messages,current_files,repository_owner)
            
            #print(commits)
            
            #print(last_deployment)
            #print(commits)
            
            filtered_commits = []
            for commit in commits:
                files = []
                deleted_files = []
                for file in commits[commit]["files"]:
                    flag = file[0][0]
                    path = file[-1]
                    if "D" in flag:
                        deleted_files.append(path)
                    else:
                        files.append( {"flag": flag, "path": path} )
                #if len(files) + len(deleted_files) == len(commits[commit]["files"]):
                commits[commit]["files"] = files
                filtered_commits.append(commits[commit])

            #print(commits)
            #print(filtered_commits)
            #print(filtered_lines)
            #print(last_deployment)
            #print(commit_lines)
            #print(committed_changes)

            filtered_files = {}
            #lines = [ele.split("\t") for ele in uncommitted_changes]
            #lines = [ele.strip().split(" ",1) for ele in uncommitted_changes]
            for line in uncommitted_changes:
                if len(line) == 1:
                    continue
                
                line = line.strip()
                flag, path = line.split(" ", 1)
                path = path.strip().strip("\"")
                if "R" in flag:
                    src_path, dest_path = path.split(" -> ", 1)
                    path = dest_path

                #print("{} {}".format(flag,path))

                if self.filterPath( flag, path, last_deployment.timestamp() ):
                    if path not in filtered_files or "A" in flag:
                        filtered_files[path] = {"flag": flag, "path": path}
                            
            files = glob.glob("{}/**/**/*".format(self.config.deployment_config_path), recursive = True)
            config_files = {}
            for filename in files:
                file_stat = os.stat(filename)
                if file_stat.st_mtime > last_deployment.timestamp():
                    path = filename[len(self.config.deployment_directory):]
                    config_files[path] = {"flag": "M", "path": path}

            lines = list(config_files.values()) + list(filtered_files.values())
            
            if len(lines) > 0:
                filtered_commits.insert(0,{"date": None, "message": "uncommitted", "files": lines})

            smartserver_changes = filtered_commits
            
        return smartserver_code, smartserver_pull, smartserver_changes
