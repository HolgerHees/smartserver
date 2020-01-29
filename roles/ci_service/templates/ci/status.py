import os

def getData(status_file):
    data = ["","",""]
    if os.path.isfile(status_file):
        with open(status_file, 'r') as f:
            data = f.readline().strip().split(":")
    return data
  
def setData(status_file,data):
    with open(status_file, 'w') as f:
        f.write(":".join(data))
  
def getStatus(status_file):
    if os.path.isfile(status_file):
        data = getData(status_file)
        if data[0] == "":
            data[0] = None
        if data[1] == "":
            data[1] = None
        if data[2] == "":
            data[2] = None
        return { "status": data[0], "git_hash": data[1], "vid": data[2], "last_modified": os.path.getmtime(status_file) }
    return None
  
def setStatus(status_file,status):
    data = getData(status_file)
    data[0] = status if status != None else ""
    setData(status_file,data)

def setGitHash(status_file,git_hash):
    data = getData(status_file)
    data[1] = git_hash if git_hash != None else ""
    setData(status_file,data)

def setVID(status_file,vid):
    data = getData(status_file)
    data[2] = vid if vid != None else ""
    setData(status_file,data)
