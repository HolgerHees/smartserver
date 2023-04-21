import os
import requests
import json
import re
from dateutil import parser

#from github import Github

from lib import helper
from lib import log

def initRepository(repository_dir, repository_url, build_dir):
  if not os.path.isdir(repository_dir) or not os.path.isdir("{}/.git".format(repository_dir)) :
      log.info("Clone repository: {} to {} ... ".format(repository_url, repository_dir), end='', flush=True)
      cloneResult = helper.execCommand( u"git clone {} {}".format(repository_url, repository_dir), repository_dir )
      if cloneResult.returncode == 0:
          log.info( u"done", flush=True )
      else:
          log.error( u"error: {}".format(cloneResult.stdout.decode("utf-8")), flush=True )

def updateRepository(repository_dir,branch):
    # git ls-remote {{vault_deployment_config_git}} HEAD
    helper.execCommand( u"git pull", repository_dir )

def getHash(repository_dir):
    checkResult = helper.execCommand( u"git rev-parse @", repository_dir )
    return checkResult.stdout.decode("utf-8").strip()

def getLog(repository_dir,git_hash):
    result = helper.execCommand( u"git show --quiet {}".format(git_hash), repository_dir )
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
