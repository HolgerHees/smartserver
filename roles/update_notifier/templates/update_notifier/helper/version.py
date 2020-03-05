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
