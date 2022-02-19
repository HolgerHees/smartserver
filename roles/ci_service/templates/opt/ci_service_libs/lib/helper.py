import subprocess
import re

from smartserver import command

def getPid(ppid,name):
    result = command.exec([ "ps", "-f", "-o", "pid,cmd", "--ppid", str(ppid) ] )
    result = result.stdout.decode("utf-8")

    m = re.search(".*{}.*".format(name), result)
    
    return m.group(0).strip().split(" ")[0] if m else ""

def execCommand(cmd, cwd=None, exitstatus_check=True ):
    return command.exec([ cmd ], shell=True, cwd=cwd, exitstatus_check=exitstatus_check )

def log( message, log_level = "info" ):
    message = message.replace("\"", "\\\"")
    execCommand( u"echo \"{}\" | systemd-cat -t ci_service -p {}".format(message,log_level) )
    
 
