import re

class Version:
    @staticmethod
    def parseVersionString(version_label,pattern):
        m = re.search(pattern,version_label)
        if m:
            return Version(m.group(1))
        
        return None
  
    def __init__(self,version_string):
        self.id_r = re.split('[^0-9]',version_string)

        if len(self.id_r) == 1:
            self.id_r.append("0")

        self.branch_string = ".".join(self.id_r[0:2])
        
        self.version_string = ".".join(self.id_r)
        
    def __repr__(self):
        return ".".join(self.id_r)
            
    def getBranchString(self):
        return self.branch_string
    
    def getVersionString(self):
        return self.version_string

    def compare(self,version):
        if self.version_string == version.version_string:
            return 0
        
        result = 1
        for index in range(len(self.id_r)):
            if index < len(version.id_r):
                if int(self.id_r[index]) > int(version.id_r[index]):
                    result = -1
                    break;
                elif int(self.id_r[index]) < int(version.id_r[index]):
                    break;
            else:
                if int(self.id_r[index]) == 0:
                    result = 0
                elif int(self.id_r[index]) > 0:
                    result = -1
                break;
        return result 
