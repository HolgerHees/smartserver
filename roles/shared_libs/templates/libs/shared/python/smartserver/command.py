import subprocess
import os
import time
import logging

def _prepareRunOnHost(cmd, cwd, env, run_on_host):
    shell = not isinstance(cmd, list)

    if run_on_host:
        if cwd is not None or env is not None:
            if not shell:
                cmd = subprocess.list2cmdline(cmd)
            shell = True
            if cwd is not None:
                cmd = "cd {} && {}".format(cwd, cmd)
            if env is not None:
                for key in env:
                    cmd = "{}={} {}".format(key, env[key], cmd)

        _cmd = [ "nsenter", "-t", "1", "--all", "--" ]
        if shell:
            _cmd += ["sh", "-c"]
            _cmd.append( cmd )
            cmd = subprocess.list2cmdline(_cmd)
        else:
            cmd = _cmd + cmd

    #logging.info(cmd)
    return shell, cmd

def popen(cmd, cwd=None, env=None, run_on_host=False):
    shell, cmd = _prepareRunOnHost(cmd, cwd, env, run_on_host)

    process = subprocess.Popen(cmd,
        bufsize=1,  # 0=unbuffered, 1=line-buffered, else buffer-size
        universal_newlines=True, encoding='utf-8', stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=cwd, env=env, shell=shell)
    return process

def exec2(cmd, cwd=None, env=None, is_running_callback=None, run_on_host=False):
    shell, cmd = _prepareRunOnHost(cmd, cwd, env, run_on_host)

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

def exec( cmd, check=False, capture_output=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=None, env=None, exitstatus_check=True, run_on_host=False):
    shell, cmd = _prepareRunOnHost(cmd, cwd, env, run_on_host)

    if not capture_output:
        stdout = subprocess.DEVNULL

    result = subprocess.run(cmd, shell=shell, check=check, stdout=stdout, stderr=stderr, cwd=cwd )
    if exitstatus_check and result.returncode != 0:
        raise Exception(result.stdout.decode("utf-8"))
    return result

def sendEmail(email, subject, message, run_on_host=False):
    exec( u"echo -e \"{}\" | mail -s \"{}\" {}".format(message, subject, email), run_on_host=run_on_host )


