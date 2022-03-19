import subprocess
import re

from smartserver import command


def execCommand(cmd, cwd=None, exitstatus_check=True ):
    return command.exec([ cmd ], shell=True, cwd=cwd, exitstatus_check=exitstatus_check )

def log( message, log_level = "info" ):
    message = message.replace("\"", "\\\"")
    execCommand( u"echo \"{}\" | systemd-cat -t ci_service -p {}".format(message,log_level) )
    
 
