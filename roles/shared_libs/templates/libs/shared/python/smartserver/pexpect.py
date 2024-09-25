import pexpect
import os
import signal
import logging
from pexpect.exceptions import EOF, TIMEOUT
import subprocess

from smartserver import processlist
from smartserver import command


class Process():
    def __init__(self, cmd, timeout=0, logfile=None, cwd=None, env=None, interaction=None, namespace_pid=None):
        self.cmd = cmd
        self.timeout = timeout
        self.logfile = logfile
        self.cwd = cwd
        self.env = env
        self.interaction = interaction
        self.namespace_pid = namespace_pid

        self.exitcode = None
        self.output = None

        self.interrupt_state = None

        self.process = None

    def terminate(self):
        self.interrupt_state = -1
        if self.process is not None:
            #if self.nsenter:
            #    child_pids = processlist.Processlist.getPids(ppid=self.process.pid)
            #    if child_pids is not None:
            #        for child_pid in child_pids:
            #            os.kill(int(child_pid), signal.SIGTERM)
            #            #logging.info(str(child_pid))
            os.kill(self.process.pid, signal.SIGTERM)

    def getExitCode(self):
        return self.exitcode

    def getOutput(self):
        return self.output

    def isTerminated(self):
        return self.interrupt_state == -1

    def isTimeout(self):
        return self.interrupt_state == -2

    def isAlive(self):
        return self.process.isalive() if self.process is not None else False

    def start(self):
        if self.interrupt_state is None:
            cmd = self.cmd
            if isinstance(cmd, list):
                cmd = subprocess.list2cmdline(cmd)

            shell, cmd = command._prepareRunOnNamespace(cmd, cwd=self.cwd, env=self.env, pid=self.namespace_pid)

            self.process = pexpect.spawn(cmd, timeout=self.timeout, cwd=self.cwd, env=self.env, encoding="utf-8" )
            if self.logfile is not None:
                self.process.logfile_read = self.logfile

            if self.interaction is not None:
                patterns = list(self.interaction.keys())
                responses = list(self.interaction.values())
            else:
                patterns = None
                responses = None

            result_list = []
            while self.process.isalive():
                try:
                    index = self.process.expect(patterns)
                    self.process.sendline(responses[index])
                    result_list.append(self.process.before)
                    result_list.append(self.process.after)
                except TIMEOUT:
                    if self.interrupt_state is None:
                        self.interrupt_state = -2
                    break
                except EOF:
                    break

            if self.process.before != '':
                result_list.append(self.process.before)

            self.process.close()

        if self.interrupt_state is None:
            self.exitcode = self.process.exitstatus
            self.output = "".join(result_list)
        else:
            self.exitcode = -1

