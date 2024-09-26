import subprocess
import os
import time
import logging

NAMESPACE_PID_HOST = 1

def _prepareRunOnNamespace(cmd, cwd, env, pid = None, uid = None):
    shell = not isinstance(cmd, list)

    if pid is not None:
        # --no-fork work's, but sideeffect is that shutting down the related container will not kill the nsenter process anymore. It will result in an inconsistent state.
        # --nofork => means the process stayes in the control group of this service
        # without --no-fork => means the process stayes in the control group of this service, but the forked exec process is part of the control group of the target namespace
        _cmd = [ "nsenter", "--target={}".format(str(pid)) ]
        if uid is not None:
            _cmd += [ "--setuid={}".format(str(uid)) ]
        if cwd is not None:
            _cmd += [ "--wdns={}".format(str(cwd)) ]
        #if env is not None:
        #    #for key in env:
        #    #    _cmd += "{}={}".format(key, env[key])
        #    _cmd += [ "--env" ]
        _cmd += [ "--all", "--" ]

        if shell:
            _cmd += ["sh", "-c"]
            _cmd.append( cmd )
            cmd = subprocess.list2cmdline(_cmd)
        else:
            cmd = _cmd + cmd

    return shell, cmd

#def _prepareRunOnHost(cmd, cwd, env, run_on_host):
#    return _prepareRunOnNamespace(cmd, cwd, env, 1 if run_on_host else None)

def popen(cmd, cwd=None, env=None, namespace_pid = None, namespace_uid = None):
    shell, cmd = _prepareRunOnNamespace(cmd, cwd, env, namespace_pid, namespace_uid)

    process = subprocess.Popen(cmd,
        bufsize=1,  # 0=unbuffered, 1=line-buffered, else buffer-size
        universal_newlines=True, encoding='utf-8', stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=cwd, env=env, shell=shell)
    return process

def exec2(cmd, cwd=None, env=None, is_running_callback=None, namespace_pid = None, namespace_uid = None):
    shell, cmd = _prepareRunOnNamespace(cmd, cwd, env, namespace_pid, namespace_uid)

    if is_running_callback is not None:
        process = subprocess.Popen(cmd,
            bufsize=1,  # 0=unbuffered, 1=line-buffered, else buffer-size
            universal_newlines=True, encoding='utf-8', stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=cwd, env=env, shell=shell )
        if process.returncode is not None:
            raise Exception("{} was not started".format(" ".join(cmd)))

        os.set_blocking(process.stdout.fileno(), False)
        while True:
            if process.poll() is not None:
                return process.returncode, process.stdout.read().strip()
            if is_running_callback():
                time.sleep(0.1)
            else:
                break
        process.terminate()
        return 0, ""
    else:
        result = subprocess.run(cmd, encoding="utf-8", shell=shell, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=cwd )
        return result.returncode, result.stdout.strip()

def exec( cmd, check=False, capture_output=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=None, env=None, exitstatus_check=True, namespace_pid = None, namespace_uid = None):
    shell, cmd = _prepareRunOnNamespace(cmd, cwd, env, namespace_pid, namespace_uid)

    if not capture_output:
        stdout = subprocess.DEVNULL

    result = subprocess.run(cmd, shell=shell, check=check, stdout=stdout, stderr=stderr, cwd=cwd )
    if exitstatus_check and result.returncode != 0:
        raise Exception(result.stdout.decode("utf-8"))
    return result

def sendEmail(email, subject, message, namespace_pid = None, namespace_uid = None):
    exec( u"echo -e \"{}\" | mail -s \"{}\" {}".format(message, subject, email), namespace_pid=namespace_pid, namespace_uid=namespace_uid )


