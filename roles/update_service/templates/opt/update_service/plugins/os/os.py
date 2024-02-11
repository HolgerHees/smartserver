import logging

class Os:
    running_cmd = []

    def _startCommand(self, cmd):
        self.running_cmd.append(" ".join(cmd))

    def _endCommand(self, cmd):
        self.running_cmd.remove(" ".join(cmd))

    def isRunning(self, cmdline):
        if len(self.running_cmd) > 0:
            for running_cmd in self.running_cmd:
                if cmdline.find(running_cmd) == 0:
                    return True
        return False
