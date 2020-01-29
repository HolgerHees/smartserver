import os
import requests
import json

#from github import Github

from ci import helper

def initRepository(repository_dir, repository_url, build_dir):
  if not os.path.isdir(repository_dir):
      print("Clone repository: {} ... ".format(repository_url), end='', flush=True)
      cloneResult = helper.execCommand( u"git clone {}".format(repository_url), build_dir )
      if cloneResult.returncode == 0:
          print( u"done", flush=True )
      else:
          print( u"error: {}".format(cloneResult.stdout.decode("utf-8")), flush=True, file=sys.stderr )

def updateRepository(repository_dir):
    # git ls-remote {{vault_deployment_config_git}} HEAD
    helper.execCommand( u"git pull", repository_dir )

def getHash(repository_dir):
    checkResult = helper.execCommand( u"git rev-parse @", repository_dir )
    return checkResult.stdout.decode("utf-8").strip()

#def initAccount(access_token):
#    return Github(access_token)
  
# https://developer.github.com/v3/repos/statuses/
def setStatus(repository_owner, access_token, git_hash, state, context, description ):
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
    if result.status_code == 201:
        helper.log( "Unable to set git status. Code: {}, Body: {}".format(result.status_code,result.text), "err" )
