import os
import requests
import json
import re

#from github import Github

from ci import helper
from ci import log

def initRepository(repository_dir, repository_url, build_dir):
  if not os.path.isdir(repository_dir):
      log.info("Clone repository: {} ... ".format(repository_url), end='', flush=True)
      cloneResult = helper.execCommand( u"git clone {}".format(repository_url), build_dir )
      if cloneResult.returncode == 0:
          log.info( u"done", flush=True )
      else:
          log.error( u"error: {}".format(cloneResult.stdout.decode("utf-8")), flush=True, file=sys.stderr )

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
    
#def initAccount(access_token):
#    return Github(access_token)
  
# https://developer.github.com/v3/repos/statuses/
def setState(repository_owner, access_token, git_hash, state, context, description ):
    headers = {
        "Authorization": "token {}".format(access_token),
        # This header allows for beta access to Checks API
        #"Accept": 'application/vnd.github.antiope-preview+json'
    }
    data = {
        "state": state,
        "context": context,
        "description": description
    }
    result = requests.post("https://api.github.com/repos/{}/statuses/{}".format(repository_owner,git_hash), headers=headers, data=json.dumps(data))
    if result.status_code != 201:
        helper.log( "Unable to set git status. Code: {}, Body: {}".format(result.status_code,result.text), "err" )
