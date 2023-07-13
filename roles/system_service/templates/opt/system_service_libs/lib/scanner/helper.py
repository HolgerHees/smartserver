import re
import subprocess
import logging
from datetime import datetime
import sys
import time

from smartserver import command

class Helper():       
    def logError(msg, caller_frame = 1):
        Helper._log(logging.error, msg, caller_frame)

    def logWarning(msg, caller_frame = 1):
        Helper._log(logging.error, msg, caller_frame)

    def logInfo(msg, caller_frame = 1):
        Helper._log(logging.info, msg, caller_frame)

    def _log(log, msg, caller_frame):
        frame = sys._getframe(caller_frame + 1)
        
        module = "{}:{}".format( frame.f_code.co_filename.replace("/",".")[:-3] , frame.f_lineno )
        module = module.ljust(25)
        module = module[-25:]
        
        log(msg, extra={"custom_module": module })

    def logProfiler(cls, start, msg):
        pass
        #logging.info("*** PROFILER *** {} - {} in {} seconds".format(cls.__class__.__name__, msg, round( (datetime.now() - start).total_seconds(), 3 ) ) )

    def dhcplisten(interface):
        return subprocess.Popen( ["/usr/bin/stdbuf", "-oL", "/usr/bin/tcpdump", "-i", interface, "-pvn", "port", "67", "or", "port", "68"],
                                bufsize=1,  # 0=unbuffered, 1=line-buffered, else buffer-size
                                universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT )

    def ping(ip, timeout, isRunningCallback = None):
        returncode, result = command.exec2(["/bin/ping", "-W", str(timeout), "-c", "1", ip ], isRunningCallback=isRunningCallback)
        return returncode == 0

    def getMacFromPing(ip, timeout, isRunningCallback = None):
        is_success = Helper.ping(ip, timeout, isRunningCallback)
        if is_success:
            return Helper.ip2mac(ip)
        return None
    
    def getMacFromArpPing(ip, interface, timeout, isRunningCallback = None):
        returncode, result = command.exec2(["/usr/sbin/arping", "-w", str(timeout), "-C", "1", "-I", interface, ip], isRunningCallback=isRunningCallback)
        if returncode != 0:
            return None

        match = re.search(r"({}) \({}\)".format("[a-z0-9]{2}:[a-z0-9]{2}:[a-z0-9]{2}:[a-z0-9]{2}:[a-z0-9]{2}:[a-z0-9]{2}",ip), result)
        if match:
            return match[1]
        return None

    def arpscan(interface, network, isRunningCallback = None):
        returncode, result = command.exec2(["/usr/local/bin/arp-scan", "--numeric", "--plain", "--timeout=2000", "--retry=1", "--interface", interface, network], isRunningCallback=isRunningCallback)
        if returncode != 0:
            raise Exception("Cmd 'arpscan' was not successful")

        arp_result = []
        for row in result.split("\n"):
            columns = row.split("\t")
            if len(columns) != 3:
                continue

            arp_result.append({"ip": columns[0], "mac": columns[1], "info": columns[2] })

        return arp_result
            
    def _nmap_parser(result, services):
        for row in result.split("\n"):
            match = re.match("([0-9]*)/([a-z]*)\s*([a-z|]*)\s*(.*)",row)
            if not match:
                continue

            if "closed" in match[3]:
                continue

            services["{}/{}".format(match[1],match[2])] = match[4]

    def nmap(ip, isRunningCallback = None):
        services = {}

        # using "--defeat-rst-ratelimit" will hit the limit of netfilter (iptables) conntrack table
        #returncode, result = command.exec2(["/usr/bin/nmap", "-n", "-p-", "-sSU", "-PN", "--defeat-rst-ratelimit", "--max-retries", "2", ip], isRunningCallback=isRunningCallback)

        # TCP scan 2 retries
        returncode, result = command.exec2(["/usr/bin/nmap", "-n", "-p-", "-sS", "-PN", "--max-retries", "2", ip], isRunningCallback=isRunningCallback)
        if returncode != 0:
            raise Exception("Cmd 'nmap' (tcp) was not successful")
        Helper._nmap_parser(result, services)

        # UDP scan with 0 retries and only first 1023 ports
        #returncode, result = command.exec2(["/usr/bin/nmap", "-n", "-p1-1023", "-sU", "-PN", "--max-retries", "0", ip], isRunningCallback=isRunningCallback)
        returncode, result = command.exec2(["/usr/bin/nmap", "-n", "-p1-1023", "-sU", "-PN", "--max-retries", "0", ip], isRunningCallback=isRunningCallback)
        if returncode != 0:
            raise Exception("Cmd 'nmap' (udp) was not successful")
        Helper._nmap_parser(result, services)

        return services

    def ip2mac(ip):
        result = command.exec(["/sbin/arp", "-n"], exitstatus_check = False)
        if result.returncode == 0:
            rows = result.stdout.decode().strip()
            match = re.search(r"\({}\) at ({})".format(ip,"[a-z0-9]{2}:[a-z0-9]{2}:[a-z0-9]{2}:[a-z0-9]{2}:[a-z0-9]{2}:[a-z0-9]{2}"), rows)
            if match:
                return match[1]
            return None

        raise Exception("Cmd 'arp' was not successful")

    def nslookup(ip):
        result = command.exec(["/usr/bin/nslookup", ip], exitstatus_check = False)
        if result.returncode == 0:
            lines = result.stdout.decode().strip().split("\n")
            for line in lines:
                data = line.split("name = ")
                if len(data) == 1:
                    continue
                if data[1]:
                    return data[1].split('.', 1)[0]
            return None

        # ip not found
        elif result.returncode == 1:
            return None

        raise Exception("Cmd 'arp' was not successful")
