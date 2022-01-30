import subprocess


def getPid(ppid,name):
    checkPidResult = execCommand( u"ps -f -o pid,cmd --ppid {} | grep -i \"{}\"".format(ppid,name) )
    pid = checkPidResult.stdout.decode("utf-8").strip().split(" ")[0];
    return pid

def execCommand(cmd, cwd=None ):
    return subprocess.run([ cmd ], shell=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=cwd )

def sendEmail(subject,message):
    execCommand( u"echo -e \"{}\" | mail -s \"{}\" root".format(message,subject) )

def log( message, log_level = "info" ):
    message = message.replace("\"", "\\\"")
    execCommand( u"echo \"{}\" | systemd-cat -t ci_service -p {}".format(message,log_level) )
    
 
