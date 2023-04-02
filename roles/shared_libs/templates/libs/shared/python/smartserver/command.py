import subprocess
import os
import time

def exec2(cmd, cwd=None, isRunningCallback=None):
    if isRunningCallback is not None:
        process = subprocess.Popen(cmd,
            bufsize=1,  # 0=unbuffered, 1=line-buffered, else buffer-size
            universal_newlines=True, encoding='utf-8', stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=cwd )
        if process.returncode is not None:
            raise Exception("{} was not started".format(" ".join(cmd)))

        os.set_blocking(process.stdout.fileno(), False)
        while True:
            if process.poll() is not None:
                return process.returncode, process.stdout.read().strip()
            if isRunningCallback():
                time.sleep(0.1)
            else:
                break
        process.terminate()
        return 0, ""
    else:
        result = subprocess.run(cmd, encoding="utf-8", shell=False, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=cwd )
        return result.returncode, result.stdout.strip()

def exec( cmd, shell=False, check=False, capture_output=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=None, exitstatus_check=True):
    if not capture_output:
        stdout = subprocess.DEVNULL
    result = subprocess.run(cmd, shell=shell, check=check, stdout=stdout, stderr=stderr, cwd=cwd )
    if exitstatus_check and result.returncode != 0:
        raise Exception(result.stdout.decode("utf-8"))
    return result
 
def sendEmail(email, subject, message):
    exec( [ u"echo -e \"{}\" | mail -s \"{}\" {}".format(message, subject, email) ], shell=True )
