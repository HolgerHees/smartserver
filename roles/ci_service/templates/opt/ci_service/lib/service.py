import sys
import os
import signal

from time import time

import logging

from lib import virtualbox

from smartserver import processlist
from smartserver import command

def checkPid(pid):
    return processlist.Processlist.checkPid(pid)

skipped_names = [
    "VBoxXPCOMIPCD",
    "VBoxSVC"
]
def checkIfSkippedName(line):
    for name in skipped_names:
        if line.find(name) != -1 or line == "":
            return True
  
def _filterProcesses(lines,processes):
    for line in lines:
        line = line.strip()
        if checkIfSkippedName(line):
            continue
        processes.append(line)
  
def getRunningProcesses(lib_dir):
    processes = []
    #ci_result = command.exec(["ps", "-a"])
    #current_pid = str(os.getpid())
    #raw_lines = ci_result.stdout.decode("utf-8").split(u"\n")
    #ci_lines = []
    #for raw_line in raw_lines:
    #    if "ci_job_handler" in raw_line and current_pid + " " not in raw_line:
    #        ci_lines.append(raw_line)
    #_filterProcesses(ci_lines,processes)
    
    vm_result = command.exec(["ps", "-a" ])
    raw_lines = vm_result.stdout.decode("utf-8").split(u"\n")
    vm_lines = []
    for raw_line in raw_lines:
        if "virtualbox" in raw_line:
            vm_lines.append(raw_line)
    _filterProcesses(vm_lines,processes)
    return processes
