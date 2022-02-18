import subprocess

def exec( cmd, shell=False, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=None, exitstatus_check=True):
    result = subprocess.run(cmd, shell=shell, check=check, stdout=stdout, stderr=stderr, cwd=cwd )
    if exitstatus_check and result.returncode != 0:
        raise Exception(result.stdout.decode("utf-8"))
    return result
 
def sendEmail(email, subject, message):
    execCommand( [ u"echo -e \"{}\" | mail -s \"{}\" {}".format(message, subject, email) ], shell=True )
