import os
import json
import re
import time
import logging

from datetime import datetime

#from github import Github

from smartserver import command


def initRepository(repository_dir, repository_url):
  if not os.path.isdir(repository_dir) or not os.path.isdir("{}/.git".format(repository_dir)) :
      logging.info("Clone repository: {} to {} ... ".format(repository_url, repository_dir), end='', flush=True)
      cloneResult = command.exec( [ "git", "clone", repository_url, repository_dir ], cwd=repository_dir )
      if cloneResult.returncode == 0:
          logging.info( u"done", flush=True )
      else:
          logging.error( u"error: {}".format(cloneResult.stdout.decode("utf-8")), flush=True )

def updateRepository(repository_dir,branch):
    # git ls-remote {{deployment_config_git}} HEAD
    count = 0
    while True:
        try:
            command.exec( [ "git", "pull" ], cwd=repository_dir )
            break
        except Exception as e:
            if count < 4:
                logging.info("Git pull problem '{}'. Retry in 15 seconds.".format(str(e)))
                time.sleep(15)
                count += 1
            else:
                raise e

#def getLastPull(repository_dir):
#    lastPullResult = command.exec( u"stat -c %Y .git/FETCH_HEAD", repository_dir )
#    lastPullTimestamp = lastPullResult.stdout.decode("utf-8").strip()
#    datetime.fromtimestamp(lastPullTimestamp)

def getHash(repository_dir):
    checkResult = command.exec( [ "git", "rev-parse", "@" ], cwd=repository_dir )
    return checkResult.stdout.decode("utf-8").strip()

def getLog(repository_dir,git_hash):
    result = command.exec( [ "git", "show", "--quiet", git_hash ], cwd=repository_dir )
    lines = result.stdout.decode("utf-8").split("\n")
    
    author = ""
    subject = ""
    is_subject = False
    for line in lines:
        line = line.strip()
        if line.startswith("Author"):
            author = re.findall(r'Author: ([^<]+).*',line)[0].strip()
        elif line.startswith("Date"):
            is_subject = True
        elif is_subject and line != "":
            subject = line
            break;
    
    return {"author":author,"subject":subject}
