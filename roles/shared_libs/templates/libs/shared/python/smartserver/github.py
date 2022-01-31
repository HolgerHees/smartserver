import requests
import json
from dateutil import parser

class GitHub():
    @staticmethod
    def getStates(repository_owner, git_hash ):
        statusUrl = "https://api.github.com/repos/{}/statuses/{}".format(repository_owner,git_hash)
        result = requests.get(statusUrl)

        if result.status_code != 200:
            raise Exception( "Unable to get git status. Code: {}, Body: {}".format(result.status_code,result.text) )

        json_result = json.loads(result.text)
        
        #print(len(json_result))
        states = {}
        for build_state in json_result:
            created_at = parser.parse(build_state["created_at"])
            
            if build_state["context"] in states:
                if states[build_state["context"]][0] < created_at:
                    states[build_state["context"]] = [created_at, build_state["state"]]
            else:
                states[build_state["context"]] = [created_at, build_state["state"]]
                
        result = {}
        for context in states:
            result[context] = states[context][1]

        return result
      
    # https://developer.github.com/v3/repos/statuses/
    @staticmethod
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
            raise Exception( "Unable to set git status. Code: {}, Body: {}".format(result.status_code,result.text) )
