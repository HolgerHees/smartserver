import time
import os
import logging
from select import select

from smartserver import command


class Process:
    SIGNAL_TERM = -15

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

        self.process = command.popen(cmd, run_on_host=True)
        #if self.has_errors:
        os.set_blocking(self.process.stdout.fileno(), False)
        while self.process.poll() is None:
            #logging.info("loop start " + str(self.process.pid))
            poll_result = select([self.process.stdout], [], [], 5)[0]
            #logging.info("loop done " + str(self.process.pid))
            if not poll_result:
                continue

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
            self.has_errors = True
        else:
            self.has_errors = False

        self.process = None
        self.is_running = False

        return time.time() - start
