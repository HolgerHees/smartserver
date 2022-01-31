import subprocess
import re

def getPid(ppid,name):
    result = subprocess.run([ "ps", "-f", "-o", "pid,cmd", "--ppid", str(ppid) ], shell=False, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT )
    result = result.stdout.decode("utf-8")

    m = re.search(".*{}.*".format(name), result)
    
    return m.group(0).strip().split(" ")[0] if m else ""

def execCommand(cmd, cwd=None ):
    return subprocess.run([ cmd ], shell=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=cwd )

def sendEmail(subject,message):
    execCommand( u"echo -e \"{}\" | mail -s \"{}\" root".format(message,subject) )

def log( message, log_level = "info" ):
    message = message.replace("\"", "\\\"")
    execCommand( u"echo \"{}\" | systemd-cat -t ci_service -p {}".format(message,log_level) )
    
 
