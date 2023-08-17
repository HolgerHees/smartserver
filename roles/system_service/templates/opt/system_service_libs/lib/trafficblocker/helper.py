import re
import subprocess
import logging
from datetime import datetime
import sys
import time

from smartserver import command

class Helper():
    @staticmethod
    def getBlockedIps():
        returncode, cmd_result = command.exec2(["/sbin/iptables", "-S", "INPUT"])
        if returncode != 0:
            raise Exception("Cmd 'iptables' was not successful")

        result = []
        for row in cmd_result.split("\n"):
            if "trafficblocker" not in row:
                continue
            match = re.match("-A INPUT -s ([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})\/32 .* -j DROP",row)
            if match:
                result.append(match[1])

        return result

    @staticmethod
    def blockIp(ip):
        returncode, cmd_result = command.exec2(["/sbin/iptables", "-I", "INPUT", "-s", "{}/32".format(ip), "-m", "comment", "--comment", "trafficblocker", "-j", "DROP"])
        if returncode != 0:
            raise Exception("Cmd 'iptables -A' was not successful")

        #returncode, cmd_result = command.exec2(["/sbin/iptables", "-I", "INPUT", "-s", "{}/32".format(ip), "-j", "LOG", "--log-prefix", "INPUT:DROP: ", "--log-level", "6" ])
        #if returncode != 0:
        #    raise Exception("Cmd 'iptables -A' was not successful")

    @staticmethod
    def unblockIp(ip):
        returncode, cmd_result = command.exec2(["/sbin/iptables", "-D", "INPUT", "-s", "{}/32".format(ip), "-m", "comment", "--comment", "trafficblocker", "-j", "DROP"])
        if returncode != 0:
            raise Exception("Cmd 'iptables -D' was not successful")

        #returncode, cmd_result = command.exec2(["/sbin/iptables", "-D", "INPUT", "-s", "{}/32".format(ip), "-j", "LOG", "--log-prefix", "INPUT:DROP: ", "--log-level", "6" ])
        #if returncode != 0:
        #    raise Exception("Cmd 'iptables -D' was not successful")
