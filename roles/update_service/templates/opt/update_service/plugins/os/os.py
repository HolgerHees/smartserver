import logging

class CmdLock():
    def __init__(self, cmd):
        self.cmd = cmd

    def __enter__(self):
        Os.running_cmd.append(" ".join(self.cmd))
        return self.cmd

    def __exit__(self, exception_type, exception_value, traceback):
        Os.running_cmd.remove(" ".join(self.cmd))

class Os:
    running_cmd = []

    def lockCmd(self, cmd):
        return CmdLock(cmd)

    def isRunning(self, cmdline):
        if len(Os.running_cmd) > 0:
            for running_cmd in Os.running_cmd:
                if cmdline.find(running_cmd) == 0:
                    return True
        return False
