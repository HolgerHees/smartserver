from ci import helper

def getRegisteredMachines():
    result = helper.execCommand("VBoxManage list vms")
    lines = result.stdout.decode("utf-8").strip().split("\n");
    machines = {}
    for line in lines:
        if len(line) > 0:
            (name,vid) = line.split(" ")
            machines[vid] = name.strip("\"")
    return machines
 
def destroyMachine(vid):
    vmCleaned = False

    if vid != None:
        machines = getRegisteredMachines()
        
        if vid in machines:
            name = machines[vid]
            print(u"VM - vid: '{}', name: '{}' - destroyed.".format(vid,name))
            helper.execCommand("VBoxManage controlvm \"{}\" poweroff".format(vid))
            helper.execCommand("VBoxManage unregistervm --delete \"{}\"".format(vid))
            vmCleaned = True
        else:
            print(u"VM - vid: '{}' not found.".format(vid))
    return vmCleaned

def checkMachines(show_info):
    machines = getRegisteredMachines()
    if len(machines.keys()) > 0:
        if show_info:
            print(u"Following machines are registered.")
        else:
            print(u"Some machines are still there. Check leftovers.")
        for vid,name in machines.items():
            print(u"  VM - vid: '{}', name: '{}'".format(vid,name))
    elif show_info:
        print(u"No machines are registered.")
  
