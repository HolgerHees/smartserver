import re

from smartserver import command


class Helper(): 
    def ip2mac(ip):
        result = command.exec(["/usr/sbin/arp", "-n"])
        rows = result.stdout.decode().strip().split("\n")
        for row in rows:
            columns = row.split("\t")
            match = re.search(r"^{}.*?({}).*$".format(ip,"[a-z0-9]{2}:[a-z0-9]{2}:[a-z0-9]{2}:[a-z0-9]{2}:[a-z0-9]{2}:[a-z0-9]{2}"), row)
            if match:
                return match[1]
        return None
    
    def arpscan(interface, network ):
        result = command.exec(["/usr/bin/arp-scan", "--interface", interface, network])
        
        rows = result.stdout.decode().strip().split("\n")
        
        arp_result = []
        for row in rows:
            columns = row.split("\t")
            if len(columns) != 3:
                continue
            
            arp_result.append({"ip": columns[0], "mac": columns[1], "info": columns[2] })
            
        return arp_result
            
    def nslookup(ip):
        result = command.exec(["/usr/bin/nslookup", ip], exitstatus_check = False)
        if result.returncode == 0:
            return result.stdout.decode().strip().split("\n")[0].split("name = ")[1]
    
        return ""
                    
