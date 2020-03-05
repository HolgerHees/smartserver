import urllib.request
import json
import re
import subprocess

from packaging import version

class Version:
    def __init__(self,version_string):
        self.version_string = version_string
        self.id_r = version_string.split(".")

        if len(self.id_r) == 1:
            self.id_r.append("0")

        self.branch = ".".join(self.id_r[0:2])
        
    def __repr__(self):
        return ".".join(self.id_r)
            
    def getBranch(self):
        return self.branch
    
    def getVersionString(self):
        return self.version_string

    def compare(self,version):
        valid = True
        for index in range(len(self.id_r)):
            if index < len(version.id_r):
                if int(self.id_r[index]) > int(version.id_r[index]):
                    valid = False
                    break;
                elif int(self.id_r[index]) < int(version.id_r[index]):
                    break;
            else:
                break;
        return valid

class Repository:
  
    REGISTRY="hub.docker.com"
    #REPOSITORY="php"
    #CURRENT_VERSION="7.3.10"
    #PATTERN="([0-9\.]+)-fpm$"
    
    repositories = None
  
    def __init__(self,repository,pattern):
        self.repository = repository
        self.pattern = pattern
        self.url = "https://{}/v1/repositories/{}/tags".format(Repository.REGISTRY,self.repository)
        
        if Repository.repositories is None:
            Repository.repositories = {}
            result = subprocess.run([ "/usr/bin/docker image list" ], shell=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=None )
            lines = result.stdout.decode("utf-8").split("\n")
            for line in lines:
                columns = line.split()
                if len(columns) == 0:
                    continue
                Repository.repositories[columns[0]] = {'tag': columns[1],'image': columns[2]}

        data = Repository.repositories[self.repository]
        m = re.search(self.pattern,data['tag'])
        self.current_version = m.group(1)
                
    def getCurrentVersion(self):
        return self.current_version

    def getCurrentBranch(self):
        return Version(self.current_version).getBranch()

    def getNewVersions(self):
        current_version = Version(self.current_version)

        last_version_r = {}

        with urllib.request.urlopen(self.url) as response:
            raw = response.read().decode("utf-8")

            data = json.loads(raw)
            
            for tag in data:
                m = re.search(self.pattern, tag['name'])
                if m is None:
                    continue
                
                version = Version(m.group(1))
                
                if current_version.compare(version):
                    if version.getBranch() in last_version_r and not last_version_r[version.getBranch()].compare(version):
                        continue

                    last_version_r[version.getBranch()] = version
                
                #if version.parse(m.group(1)) > version.parse(CURRENT_VERSION):
                #    print(m.group(1))
            
        new_version_r = {}
        for branch in last_version_r:
            new_version_r[branch] = last_version_r[branch].getVersionString()
                  
        return new_version_r

#print(data)
