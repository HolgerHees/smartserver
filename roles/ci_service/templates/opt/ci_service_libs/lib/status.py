import os

def getData(status_file):
    data = ["","","","",""]
    if os.path.isfile(status_file):
        with open(status_file, 'r') as f:
            data = f.readline().strip().split(":")
    return data
  
def setData(status_file,data):
    with open(status_file, 'w') as f:
        f.write(":".join(data))
  
def getState(status_file):
    if os.path.isfile(status_file):
        data = getData(status_file)
        if data[0] == "":
            data[0] = None
        if data[1] == "":
            data[1] = None
        if data[2] == "":
            data[2] = None
        if data[3] == "":
            data[3] = None
        if data[4] == "":
            data[4] = None
        return { "status": data[0], "config": data[1], "deployment": data[2], "git_hash": data[3], "vid": data[4], "last_modified": os.path.getmtime(status_file) }
    return None
  
def setState(status_file,status):
    data = getData(status_file)
    data[0] = status if status != None else ""
    setData(status_file,data)

def setDeployment(status_file,config,deployment):
    data = getData(status_file)
    data[1] = config if config != None else ""
    data[2] = deployment if deployment != None else ""
    setData(status_file,data)

def setGitHash(status_file,git_hash):
    data = getData(status_file)
    data[3] = git_hash if git_hash != None else ""
    setData(status_file,data)

def setVID(status_file,vid):
    data = getData(status_file)
    data[4] = vid if vid != None else ""
    setData(status_file,data)
