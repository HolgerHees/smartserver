import time
import os
import logging
from select import select

from smartserver import command


class Process:
    SIGNAL_KILL = -9
    SIGNAL_TERM = -15

    process_container_pid = None
    process_container_uid = None

    @staticmethod
    def init(uid):
        Process.process_container_uid = uid

    @staticmethod
    def detectProcessContainerPID():
        if Process.process_container_pid is None:
            returncode, result = command.exec2("pgrep -f \"master\" -U {}".format(Process.process_container_uid))
            if returncode == 0:
                Process.process_container_pid = result.split(" ")[0]
        return Process.process_container_pid

    @staticmethod
    def resetProcessContainerPID():
        Process.process_container_pid = None

    def __init__(self):
        self.process = None

        self.has_errors = False
        self.is_running = False
        self.returncode = None

    def terminate(self):
        if not self.is_running:
            return

        self.is_running = False
        if self.process is not None:
            self.process.kill()

    def join(self):
        if self.process is not None:
            self.returncode = self.process.wait()

    def hasErrors(self):
        return self.has_errors

    def isShutdown(self):
        return self.returncode == Process.SIGNAL_TERM

    def run(self, cmd, logging_callback):
        start = time.time()
        self.is_running = True
        self.returncode = None

        pid = Process.detectProcessContainerPID()
        if pid is not None:
            self.process = command.popen(cmd, namespace_pid = pid, namespace_uid = Process.process_container_uid)
            #if self.has_errors:
            os.set_blocking(self.process.stdout.fileno(), False)
            while self.process.poll() is None:
                #logging.info("loop start " + str(self.process.pid))
                poll_result = select([self.process.stdout], [], [], 5)[0]
                #logging.info("loop done " + str(self.process.pid))
                if poll_result:
                    for line in iter(self.process.stdout.readline, b''):
                        if line == '':
                            break
                        logging_callback(line.strip())

                if self.has_errors:
                    if time.time() - start > 5:
                        self.has_errors = False
                        #os.set_blocking(self.process.stdout.fileno(), True)
                    #time.sleep(0.1)

            #logging.info("run done " + " ".join(cmd))

            self.returncode = self.process.returncode
            if self.is_running and self.returncode not in [0,Process.SIGNAL_TERM]:
                Process.resetProcessContainerPID()
                self.has_errors = True
            else:
                self.has_errors = False
        else:
            self.returncode = Process.SIGNAL_KILL
            self.has_errors = True

        self.process = None
        self.is_running = False

        return time.time() - start
