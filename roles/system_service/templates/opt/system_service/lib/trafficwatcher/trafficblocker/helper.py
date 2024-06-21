import re
import subprocess
import logging
from datetime import datetime
import sys
import time

from smartserver import command

class Helper():
    @staticmethod
    def _fetchBlockedIps(result, cmd, regex):
        returncode, cmd_result = command.exec2(cmd)
        if returncode != 0:
            raise Exception("Cmd '{}' was not successful".format(" ",join(cmd)))

        for row in cmd_result.split("\n"):
            if "trafficblocker" not in row:
                continue
            match = re.match("-A INPUT -s {} .* -j DROP".format(regex) ,row)
            if match:
                result.append(match[1])

    @staticmethod
    def getBlockedIps():
        result = []
        Helper._fetchBlockedIps(result, ["/sbin/iptables", "-S", "INPUT"], r"([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})/32")
        Helper._fetchBlockedIps(result, ["/sbin/ip6tables", "-S", "INPUT"], r"([0-9a-z:]*)/128")
        return result

    @staticmethod
    def _modifyBlockedIps(cmd):
        returncode, cmd_result = command.exec2(cmd)
        if returncode != 0:
            raise Exception("Cmd '{}' was not successful".format(" ",join(cmd)))

    @staticmethod
    def blockIp(ip):
        if ":" in ip:
            cmd = ["/sbin/ip6tables", "-I", "INPUT", "-s", "{}/128".format(ip), "-m", "comment", "--comment", "trafficblocker", "-j", "DROP"]
        else:
            cmd = ["/sbin/iptables", "-I", "INPUT", "-s", "{}/32".format(ip), "-m", "comment", "--comment", "trafficblocker", "-j", "DROP"]
        Helper._modifyBlockedIps(cmd)

    @staticmethod
    def unblockIp(ip):
        if ":" in ip:
            cmd = ["/sbin/ip6tables", "-D", "INPUT", "-s", "{}/128".format(ip), "-m", "comment", "--comment", "trafficblocker", "-j", "DROP"]
        else:
            cmd = ["/sbin/iptables", "-D", "INPUT", "-s", "{}/32".format(ip), "-m", "comment", "--comment", "trafficblocker", "-j", "DROP"]
        Helper._modifyBlockedIps(cmd)
