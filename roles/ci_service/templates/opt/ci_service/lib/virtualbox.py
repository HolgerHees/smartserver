import os

from lib import helper
from lib import log

def deltree(target):
    for d in os.listdir(target):
        try:
            deltree(target + '/' + d)
        except OSError:
            os.remove(target + '/' + d)

    os.rmdir(target)

def getRegisteredMachines():
    result = helper.execCommand("VBoxManage list vms")
    lines = result.stdout.decode("utf-8").strip().split("\n");
    machines = {}
    for line in lines:
        if len(line) > 0:
            (name,vid) = line.split(" ")
            machines[vid] = name.strip("\"")
    return machines

def getMachineLeftovers(lib_dir, machines):
    machine_names = []
    for vid,name in machines.items():
        machine_names.append(name)

    leftovers = {}
    for file in os.listdir("{}VirtualMachines".format(lib_dir)):
        if file not in machine_names:
            leftovers[file] = "{}VirtualMachines/{}".format(lib_dir,file)
    return leftovers
 
def destroyMachine(vid):
    vmCleaned = False
    if vid != None:
        machines = getRegisteredMachines()
        if vid in machines:
            name = machines[vid]
            log.info(u"VM - vid: '{}', name: '{}' - destroyed.".format(vid,name))
            helper.execCommand("VBoxManage controlvm \"{}\" poweroff".format(vid), exitstatus_check=False)
            helper.execCommand("VBoxManage unregistervm --delete \"{}\"".format(vid), exitstatus_check=False)
            
            vmCleaned = True
        else:
            log.error(u"VM - vid: '{}' not found.".format(vid))
    return vmCleaned

def destroyMachineLeftover(leftover,lib_dir,machines):
    leftoverCleaned = False
    if leftover != None:
        leftovers = getMachineLeftovers(lib_dir,machines)
        if leftover in leftovers:
            log.info(u"Leftover: '{}' cleaned.".format(leftover))
            deltree(leftovers[leftover])
            leftoverCleaned = True
        else:
            log.error(u"Leftover: '{}' not found.".format(leftover))
    return leftoverCleaned

def checkMachines(lib_dir, show_info):
    machines = getRegisteredMachines()
    if len(machines.keys()) > 0:
        if show_info:
            log.info(u"Following machines are registered.")
            for vid,name in machines.items():
                log.info(u"  VM - vid: '{}', name: '{}'".format(vid,name))
        else:
            log.info(u"Some machines are still there.")
    elif show_info:
        log.info(u"No machines are registered.")
        
    leftovers = getMachineLeftovers(lib_dir, machines)
    if len(leftovers.keys()) > 0:
        if show_info:
            log.info(u"Following leftovers found.")
            for leftover in leftovers:
                log.info(u"  LO - name: '{}', path: '{}'".format(leftover,leftovers[leftover]))
        else:
            log.info(u"Some leftovers are still there.")
    elif show_info:
        log.info(u"No machine leftovers found.")
        
