import re
import subprocess

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

    def arpping(interface, ip, timeout):
        return subprocess.run(["/usr/sbin/arping", "-w", str(timeout), "-C", "1", "-I", interface, ip ], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

    def ping(ip):
        return subprocess.run(["/bin/ping", "-c", "1", ip ], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

    def arpscan(interface, network ):
        result = command.exec(["/usr/local/bin/arp-scan", "--interface", interface, network])
        
        rows = result.stdout.decode().strip().split("\n")
        
        arp_result = []
        for row in rows:
            columns = row.split("\t")
            if len(columns) != 3:
                continue
            
            arp_result.append({"ip": columns[0], "mac": columns[1], "info": columns[2] })
            
        return arp_result
            
    def ip2mac(ip):
        result = command.exec(["/sbin/arp", "-n"])
        if result.returncode == 0:
            rows = result.stdout.decode().strip().split("\n")
            for row in rows:
                columns = row.split("\t")
                match = re.search(r"{}.*?({}).*$".format(ip,"[a-z0-9]{2}:[a-z0-9]{2}:[a-z0-9]{2}:[a-z0-9]{2}:[a-z0-9]{2}:[a-z0-9]{2}"), row)
                if match:
                    return match[1]
                
        Helper.ping(ip)
        
        return None

    def nslookup(ip):
        result = command.exec(["/usr/bin/nslookup", ip], exitstatus_check = False)
        if result.returncode == 0:
            lines = result.stdout.decode().strip().split("\n")
            for line in lines:
                data = line.split("name = ")
                if len(data) == 1:
                    continue
                if data[1]:
                    return data[1]
        return None
