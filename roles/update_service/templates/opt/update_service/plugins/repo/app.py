import abc
import urllib.request

import urllib.error
import http.client
import traceback
import sys

import time

from helper.version import Version

#class SkipableVersionError(Exception):
#    pass
  
class App:
    def __init__(self,job_config):
        self.name = job_config['name']
        self.type = job_config['type']
        self.url = job_config['url']

    def getName(self):
        return self.name

    def getType(self):
        return self.type

    def getUrl(self):
        return self.url

    def _filterPossibleVersions(self,current_version,last_updates):
        current_updates_r = {}
        if last_updates is not None:
            for last_update in last_updates:
                version = Version(last_update['version'])
                if current_version.compare(version) < 1:
                    continue
                current_updates_r[version.getBranchString()] = [ version, last_update['date'], None ]
        return current_updates_r

    def _updateCurrentUpdates(self,version,current_updates_r,tag):
        if version.getBranchString() in current_updates_r and current_updates_r[version.getBranchString()][0].compare(version) == 0:
            current_updates_r[version.getBranchString()][2] = tag

    def _isNewUpdate(self,version,current_updates_r,current_version):
        if current_version.compare(version) == 1:
            if version.getBranchString() in current_updates_r and current_updates_r[version.getBranchString()][0].compare(version) < 1:
                return False
            #print(current_updates_r)
            #print(version)
            return True
        return False
    
    def _registerNewUpdate(self,current_updates_r, version, date, tag):
        current_updates_r[version.getBranchString()] = [ version, date, tag ]

    def _convertUpdates(self,current_updates_r,project):
        new_updates_r = {}
        for branch in current_updates_r:
            version = current_updates_r[branch]
            if version[2] is None:
                # ignore versions which are not valid anymore
                continue
                #raise Exception('Tag missing in version data in project {} version {}'.format(project,version[0].getVersionString()))
            new_updates_r[branch] = self._createUpdate( version = version[0].getVersionString(), branch = branch, date = version[1], url = self._getUpdateUrl(version[2]) )
        return new_updates_r
    
    def _createUpdate(self,version,branch,date,url):
        return { 'version': version, 'branch': branch, 'date': date, 'url': url }
    
    def _requestUrl(self,req,count = 0):
        #print("request url '{}'".format( req.get_full_url() ) )
        try:
            with urllib.request.urlopen(req) as response:
                try:
                    raw = response.read().decode("utf-8")
                    exception = None
                except (http.client.IncompleteRead) as e:
                    raw = None
                    exception = e
        except (urllib.error.URLError) as e:
            if isinstance(e,urllib.error.HTTPError) and e.code == 404:
                body = e.read().decode()
                #if "errors" in body:
                raise Exception(body)
                #raise SkipableVersionError()
            raw = None
            exception = e

        # handle retry outside the exception block
        if raw is None:
            count = count + 1
            if count >= 5:
                print("Traceback (most recent call last):",file=sys.stderr)
                traceback.print_tb(exception.__traceback__)
                print("Exception:  {}".format(exception),file=sys.stderr)
                print("----",file=sys.stderr)
                raise Exception('More then 5 retries to fetch data from url {}'.format(req.get_full_url()))
            time.sleep(count * 4)
            return self._requestUrl(req,count)
        
        return raw
    
    @abc.abstractmethod
    def _getUpdateUrl(self,tag = None):
        return
