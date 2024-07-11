import os
import logging

from smartserver import command
from smartserver import nsenter


def deltree(target):
    for d in os.listdir(target):
        try:
            deltree(target + '/' + d)
        except OSError:
            os.remove(target + '/' + d)

    os.rmdir(target)

def getRegisteredMachines():
    with nsenter.Host():
        result = command.exec([ "VBoxManage", "list", "vms" ])
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
 
def destroyMachines(machines):
    destroyed = []
    for vid in machines.keys():
        name = destroyMachine(vid)
        destroyed.append({"vid": vid, "name": name})
    return destroyed

def destroyMachine(vid):
    if vid != None:
        machines = getRegisteredMachines()
        if vid in machines:
            name = machines[vid]
            with nsenter.Host():
                command.exec( [ "VBoxManage", "controlvm", vid, "poweroff" ], exitstatus_check=False)
                command.exec( [ "VBoxManage", "unregistervm", "--delete", vid ], exitstatus_check=False)
            return name
    return None

def destroyMachineLeftover(leftover,lib_dir,machines):
    if leftover != None:
        leftovers = getMachineLeftovers(lib_dir,machines)
        if leftover in leftovers:
            deltree(leftovers[leftover])
            return leftover
    return None

def destroyMachinesLeftovers(lib_dir,machines):
    destroyed = []
    leftovers = getMachineLeftovers(lib_dir,machines)
    for leftover in leftovers:
        name = destroyMachineLeftover(leftover,lib_dir,machines)
        destroyed.append({"name": name})
    return destroyed

def getAllMachines(lib_dir):
    machines = getRegisteredMachines()
    leftovers = getMachineLeftovers(lib_dir, machines)
    return [ machines, leftovers ]

