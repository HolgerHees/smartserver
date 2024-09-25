import urllib.request
import json
import subprocess
from datetime import datetime, timezone

from helper.version import Version

from smartserver import command

import re

from plugins.repo.app import App
#, SkipableVersionError
from config import config


class Repository(object):
    def __init__(self,job_config,global_config, operating_system):
        self.job_config = job_config
        self.global_config = global_config

    def getApplications(self, limit):
        app = Application(self.job_config, self.global_config)
        if limit is None or limit == app.getName():
            return [app]
        return None

class Application(App):
    API_BASE = "https://registry-1.docker.io/v2/"
    WEB_BASE = "https://hub.docker.com/"

    repositories = None
  
    def __init__(self,job_config,global_config):
        super().__init__(job_config)

        self.plugin_config = job_config["config"]
        self.build_dir = config.build_dir

    def checkForUpdates(self):

        self.repository = self.plugin_config['repository']
        if self.repository.find("/") == -1:
            self.repository = "library/{}".format(self.repository)

        self.pattern = self.plugin_config['pattern']
        
        version = None
        tag = None
        tag_r = []

        # parse for parent images first, because new "docker buildx" will never cache parent images.
        result = command.exec("/usr/bin/grep -R 'FROM {}:' {}*/Dockerfile".format(self.plugin_config['repository'], self.build_dir), exitstatus_check = False)
        if result.returncode == 0:
            rows = result.stdout.decode("utf-8").split("\n")
            for row in rows:
                if row == "":
                    continue
                prefix, reference = row.split("FROM ")

                _, tag = reference.split(":")
                if tag not in tag_r:
                    tag_r.append(tag)

                _version = Version.parseVersionString(tag, self.pattern)
                if version is None or _version.compare(version) == -1:
                    version = _version
        else:
            if Application.repositories is None:
                Application.repositories = {}

                result = command.exec(["podman", "image", "list", "--format", "'{{json .}}'"])
                lines = result.stdout.decode("utf-8").split("\n")
                for line in lines:
                    if line == "":
                        continue

                    obj = json.loads(line[1:-1])
                    if obj["repository"] is None or obj["repository"] == '<none>':
                        continue

                    name = obj["repository"].split("/", 1)[1]

                    if name not in Application.repositories:
                        Application.repositories[name] = []

                    Application.repositories[name].append({'tag': obj["tag"],'image': obj["Id"]})

            data_r = Application.repositories[self.plugin_config['repository']]
            for data in data_r:
                _version = Version.parseVersionString(data['tag'],self.pattern)
                if _version is not None and (version is None or version.compare(_version) == 1):
                    version = _version
                    tag = data['tag']
                tag_r.append(data['tag'])

        if version:
            self.current_version = version.getVersionString()
            self.current_tag = tag
        else:
            raise Exception('Can\'t find current version with pattern \'{}\'. Available versions are {}'.format(self.pattern, tag_r))
              
        url = "https://auth.docker.io/token?service=registry.docker.io&scope=repository:{}:pull".format(self.repository)
        token_result = self._requestData(url)
        self.token = token_result['token']

    def _getUpdateUrl(self,tag = None):
        if tag != None:
            if self.repository.startswith("library/"):
                return "{}_/{}?tab=tags&name={}".format(Application.WEB_BASE,self.repository[8:],tag)
            else:
                return "{}r/{}/tags?name={}".format(Application.WEB_BASE,self.repository,tag)
        else:
            return "{}r/{}/tags".format(Application.WEB_BASE,self.repository)
          
    def _requestData(self,url,token=None,count=0,headers={}):
        req = urllib.request.Request(url)
        if token != None:
            req.add_header('Authorization', "Bearer {}".format(token))

        for key, value in headers.items():
            #print("{}: {}".format(key,value))
            req.add_header(key, value)
        raw = self._requestUrl(req)
        data = json.loads(raw)
        return data
      
    def _getCreationDate(self,tag):
        url = "{}{}/manifests/{}".format(Application.API_BASE,self.repository,tag)
        accept = [
            "application/vnd.docker.distribution.manifest.v1+json",
            "application/vnd.docker.distribution.manifest.v1+prettyjws",
            "application/vnd.docker.distribution.manifest.v1+json",
            "application/vnd.docker.distribution.manifest.v2+json",
            "application/vnd.docker.distribution.manifest.list.v2+json",
            "application/vnd.docker.container.image.v1+json",
            "application/vnd.docker.image.rootfs.diff.tar.gzip",
            "application/vnd.docker.image.rootfs.foreign.diff.tar.gzip",
            "application/vnd.docker.plugin.v1+json",
            "application/vnd.oci.image.index.v1+json",
            "application/vnd.oci.image.manifest.v1+json"
        ]

        image_data_r = self._requestData(url,self.token,headers={"Accept": ",".join(accept)})
        if  image_data_r["mediaType"].startswith("application/vnd.docker") and 'history' in image_data_r:
            for image_raw_data in image_data_r['history']:
                image_data = json.loads(image_raw_data['v1Compatibility'])
                date = re.sub("\.[0-9]+Z","Z",image_data['created'])
                return date
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        #raise Exception('No able to fetch creation date from docker repository {} and tag {}'.format(self.repository,tag))
          
    def getCurrentVersion(self):
        branch = Version(self.current_version).getBranchString()
        
        creationDate = self._getCreationDate(self.current_tag)
        return self._createUpdate( version = self.current_version, branch = branch, date = creationDate, url = self._getUpdateUrl(self.current_tag) )

    def getCurrentVersionString(self):
        return self.current_version

    def getUpdates(self, last_updates):
        current_version = Version(self.current_version)
        current_updates_r = self._filterPossibleVersions(current_version=current_version,last_updates=last_updates)
        
        url = "{}{}/tags/list".format(Application.API_BASE,self.repository)
        data = self._requestData(url,self.token)

        for tag in data['tags']:
            version = Version.parseVersionString(tag,self.pattern)
            if version is None:
                continue
            
            self._updateCurrentUpdates(version=version,current_updates_r=current_updates_r,tag=tag)
            
            if self._isNewUpdate(version=version,current_updates_r=current_updates_r,current_version=current_version):
                update_time = self._getCreationDate(tag)
                self._registerNewUpdate(current_updates_r=current_updates_r, version=version, date=update_time, tag=tag )

        new_updates_r = self._convertUpdates(current_updates_r=current_updates_r,project=self.repository)
        return new_updates_r

#print(data)
