import re
import subprocess
import logging

from smartserver import command

class Helper():       
    #def arp():
    #    result = command.exec(["/usr/bin/arp", "-n"])
    #    rows = result.stdout.decode().strip().split("\n")

    #    arp_result = []
    #    for row in rows:
    #        columns = row.split("\t")
    #        if len(columns) != 3:
    #            continue
            
    #        arp_result.append({"ip": columns[0], "mac": columns[1], "info": columns[2] })
            
    #    return arp_result
    
    def dhcplisten(interface):
        return subprocess.Popen( ["/usr/bin/stdbuf", "-oL", "/usr/bin/tcpdump", "-i", interface, "-pvn", "port", "67", "or", "port", "68"],
                                bufsize=1,  # 0=unbuffered, 1=line-buffered, else buffer-size
                                universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT )

    def arpping(ip, mac, interface, timeout):
        result = command.exec(["/usr/sbin/arping", "-w", str(timeout), "-C", "1", "-I", interface, ip], exitstatus_check = False)
        is_success = result.returncode == 0
        if is_success:
            found = False
            rows = result.stdout.decode().strip().split("\n")
            for row in rows:
                # 0c:c4:13:18:ad:83 (192.168.0.69)
                if re.search(r"{} \({}\)".format(mac,ip), row):
                    found = True
            if not found:
                is_success = False
        return is_success

    def ping(ip, mac = None, interface = None):
        process = subprocess.run(["/bin/ping", "-c", "1", ip ], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        is_success = process.returncode == 0
        if is_success and mac is not None and interface is not None:
            if mac != Helper.ip2mac(ip, interface):
                is_success = False
        return is_success

    def nmap(ip):
        result = command.exec(["/usr/bin/nmap", "-sS", "-PN", ip], exitstatus_check = False)
        if result.returncode == 0:
            rows = result.stdout.decode().strip().split("\n")
            services = {}
            for row in rows:
                match = re.match("([0-9]*)/([a-z]*)\s*([a-z]*)\s*(.*)",row)
                if not match:
                    continue
            
                services[match[1]] = match[4]
                #ports.append({"port": match[1], "type": match[2], "state": match[3], "service": match[4] })
            return services
        else:
            raise Exception("Cmd 'nmap' was not successful")
        
    def arpscan(interface, network ):
        result = command.exec(["/usr/local/bin/arp-scan", "--interface", interface, network], exitstatus_check = False)
        if result.returncode == 0:
            rows = result.stdout.decode().strip().split("\n")
            
            arp_result = []
            for row in rows:
                columns = row.split("\t")
                if len(columns) != 3:
                    continue
                
                arp_result.append({"ip": columns[0], "mac": columns[1], "info": columns[2] })
                
            return arp_result

        raise Exception("Cmd 'arp-scan' was not successful")
            
    #def _checkMAC(mac, interface):
    #    result = command.exec(["/sbin/arp", "-n"])
    #    if result.returncode == 0:
    #        rows = result.stdout.decode().strip()
    #        return mac in rows
    #    raise Exception("Cmd 'arp' was not successful")
        
    def ip2mac(ip, interface):
        result = command.exec(["/sbin/arp", "-n"], exitstatus_check = False)
        if result.returncode == 0:
            rows = result.stdout.decode().strip().split("\n")
            for row in rows:
                columns = row.split("\t")
                match = re.search(r"\({}\).*?({}).*$".format(ip,"[a-z0-9]{2}:[a-z0-9]{2}:[a-z0-9]{2}:[a-z0-9]{2}:[a-z0-9]{2}:[a-z0-9]{2}"), row)
                if match:
                    return match[1]
            return None

        raise Exception("Cmd 'arp' was not successful")
        
                
        # fallback for devices from other networks
        #result = command.exec(["/usr/local/bin/arp-scan", "--interface", interface, "{}/32".format(ip)])
        #if result.returncode == 0:
        #    rows = result.stdout.decode().strip().split("\n")
        #    for row in rows:
        #        columns = row.split("\t")
                
        #        if len(columns) != 3:
        #            continue
                
        #        return columns[1]

    def nslookup(ip):
        result = command.exec(["/usr/bin/nslookup", ip], exitstatus_check = False)
        if result.returncode == 0:
            lines = result.stdout.decode().strip().split("\n")
            for line in lines:
                data = line.split("name = ")
                if len(data) == 1:
                    continue
                if data[1]:
                    if data[1].endswith('.fritz.box'):
                        data[1] = data[1][0:-10]
                    return data[1]
            return None

        # ip not found
        elif result.returncode == 1:
            return None

        raise Exception("Cmd 'arp' was not successful")
