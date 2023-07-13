import queue
import threading
import logging
import traceback
import time
import socket
import ipaddress

import requests
import json

import schedule
import os

from lib.helper import Helper

class IPCache(threading.Thread):
    TYPE_LOCATION = "Location"
    TYPE_UNKNOWN = "Unknown"
    TYPE_PRIVATE = "Private"

    public_networks = []

    def __init__(self, config):
        threading.Thread.__init__(self)

        for network in config.public_networks:
            network = ipaddress.ip_network(network)
            #if network.is_private:
            #    continue
            self.public_networks.append(network)

        self.max_location_cache_age = 60 * 60 * 24 * 7
        self.max_hostname_cache_age = 60 * 60 * 24 * 1

        self.is_running = False

        self.queue = queue.Queue()

        self.counter_lock = threading.Lock()
        self.counter_values = {"location_fetch": 0, "location_cache": 0, "hostname_fetch": 0, "hostname_cache": 0}

        self.dump_path = "/var/lib/system_service/ip_cache.json"

        self.version = 3

        self.valid_cache_file = True

        self.ip2location_url = "http://ip-api.com/json/{}?fields=continent,continentCode,country,countryCode,region,regionName,city,district,zip,lat,lon,org,isp,status,message"
        #self.ip2location_url = "https://api.hostip.info/get_json.php?ip={}"
        self.ip2location_state = True
        self.ip2location_throttled_until = 0

        self.location_lock = threading.Lock()
        self.hostname_lock = threading.Lock()

        self.ip2location_map = {}
        self.hostname_map = {}

    def isExternal(self, address):
        if address.is_global:
            if not self.public_networks:
                return True
            for network in self.public_networks:
                if address in network:
                    return False
            return True

        return False

    def start(self):
        self.is_running = True
        schedule.every().day.at("01:00").do(self._dump)
        schedule.every().hour.at("00:00").do(self._cleanup)
        self._restore()
        super().start()

    def terminate(self):
        if self.is_running and os.path.exists(self.dump_path):
            self._dump()
        self.is_running = False

    def run(self):
        logging.info("IP cache started")
        try:
            if not os.path.exists(self.dump_path):
                self._dump()

            while self.is_running:
                try:
                    type, ip = self.queue.get(timeout=0.5)
                    if type == "location":
                        self._resolveLocationData(ip)
                    elif type == "hostname":
                        self._resolveHostnameData(ip)
                except queue.Empty:
                    pass
            logging.info("IP cache stopped")
        except Exception:
            logging.error(traceback.format_exc())
            self.is_running = False

    def _restore(self):
        self.valid_cache_file, data = Helper.loadConfig(self.dump_path, self.version )
        if data is not None:
            self.ip2location_map = data["ip2location_map"]
            self.hostname_map = data["hostname_map"]
            logging.info("Loaded {} locations and {} hostnames".format(len(self.ip2location_map),len(self.hostname_map)))

    def _dump(self):
        if self.valid_cache_file:
            with self.location_lock:
                with self.hostname_lock:
                    Helper.saveConfig(self.dump_path, self.version, { "ip2location_map": self.ip2location_map, "hostname_map": self.hostname_map } )
                    logging.info("Saved {} locations and {} hostnames".format(len(self.ip2location_map),len(self.hostname_map)))

    def _cleanup(self):
        _now = time.time()
        location_count = 0
        with self.location_lock:
            for _ip in list(self.ip2location_map.keys()):
                if _now - self.ip2location_map[_ip]["time"] > self.max_location_cache_age:
                    del self.ip2location_map[_ip]
                    location_count += 1
        if location_count > 0:
            logging.info("Cleaned {} locations".format(location_count))

        hostname_count = 0
        with self.hostname_lock:
            for _ip in list(self.hostname_map.keys()):
                if _now - self.hostname_map[_ip]["time"] > self.max_hostname_cache_age:
                    del self.hostname_map[_ip]
                    hostname_count += 1
        if hostname_count > 0:
            logging.info("Cleaned {} hostnames".format(hostname_count))

    def _increaseStats(self, type):
        with self.counter_lock:
            self.counter_values[type] += 1

    def getCountStats(self):
        with self.counter_lock:
            counter_values = self.counter_values
            self.counter_values = {"location_fetch": 0, "location_cache": 0, "hostname_fetch": 0, "hostname_cache": 0}
        return counter_values

    def getLocationSize(self):
        return len(self.ip2location_map)

    def getLocation(self, ip, threaded):
        _ip = ip.compressed
        location = self.ip2location_map.get(_ip, None)
        if location is not None:
            #print("cachedLocation {}".format(ip))
            self._increaseStats("location_cache")
        elif threaded:
            self.queue.put(["location", ip])
            return None
        else:
            location = self._resolveLocationData(ip)
            if location is None:
                location = self._getUnknownLocationData(None)

        return location["data"]

    def _getUnknownLocationData(self, _now):
        return { "data": { "type": IPCache.TYPE_UNKNOWN }, "time": _now }

    def _getPrivateLocationData(self, _now):
        return { "data": { "type": IPCache.TYPE_PRIVATE }, "time": _now }

    def _checkField(self, key, data, fallback):
        if key not in data or data[key] == "":
            data[key] = fallback

    def _prepareField(self, key, data):
        return data[key].title().replace(" ","\\ ").replace(",","\\,")

    def _resolveLocationData(self, ip):
        _now = time.time()
        if self.ip2location_throttled_until > 0:
            if _now < self.ip2location_throttled_until:
                return None
            else:
                logging.info("Resume from throttled requests")
                self.ip2location_throttled_until = 0

        _ip = ip.compressed
        location = self.ip2location_map.get(_ip, None)
        if location is None:
            if not ip.is_global:
                self._increaseStats("location_cache")
                location = self._getPrivateLocationData(_now)
                with self.location_lock:
                    self.ip2location_map[_ip] = location
            else:
                try:
                    response = requests.get(self.ip2location_url.format(_ip))
                except:
                    logging.error("Error fetching ip {}".format(_ip))
                    logging.error(traceback.format_exc())
                    return None

                if response.status_code == 429:
                    logging.info("Rate limit is reached. Throttle requests for next 15 seconds".format(_ip))
                    self.ip2location_throttled_until = _now + 15
                    return None
                elif response.status_code == 200:
                    self._increaseStats("location_fetch")
                    if len(response.content) > 0:
                        try:
                            data = json.loads(response.content)
                        except:
                            logging.error("Error parsing ip {}".format(_ip))
                            logging.error(":{}:".format(response.content))
                            logging.error(traceback.format_exc())
                            return None

                        if data["status"] == "success":
                            location = { "data": {
                                "type": IPCache.TYPE_LOCATION,
                                "continent_name": data["continent"],
                                "continent_code": data["continentCode"].lower(),
                                "country_name": data["country"],
                                "country_code": data["countryCode"].lower(),
                                "region_name": data["regionName"],
                                "region_code": data["region"].lower(),
                                "zip": data["zip"],
                                "city": data["city"],
                                "district": data["district"], # optional, default = ""
                                "lat": data["lat"],
                                "lon": data["lon"],
                                "org": data["org"],
                                "isp": data["isp"]
                                }, "time": _now }
                        elif data["status"] == "fail":
                            if "private" in data["message"] or "reserved" in data["message"]:
                                location = self._getPrivateLocationData(_now)
                            else:
                                logging.error("Unhandled result: {}".format(response.content))
                                return None
                        else:
                            logging.error("Unhandled result: {}".format(response.content))
                            return None

                        #if "Private" in data["country_name"]:
                        #    location = { "data": {"country_name": "Private", "country_code": "xx", "city": "Private" }, "time": _now }
                        #else:
                        #    if "Unknown" in data["country_name"]:
                        #        data["country_name"] = "Unknown"
                        #        data["country_code"] = "xx"
                        #        data["city"] = "Unknown"
                        #    location = { "data": {"country_name": data["country_name"].title().replace(" ","\\ ").replace(",","\\,"), "country_code": data["country_code"].lower(), "city": data["city"].replace(" ","\\ ").replace(",","\\,") }, "time": _now }
                    else:
                        location = self._getUnknownLocationData(_now)
                    with self.location_lock:
                        self.ip2location_map[_ip] = location
                    self.ip2location_state = True
                else:
                    self.ip2location_state = False
                    return None
        else:
            self._increaseStats("location_cache")

        return location

    def getHostnameSize(self):
        return len(self.hostname_map)

    def getHostname(self, ip, threaded):
        _ip = ip.compressed
        hostname = self.hostname_map.get(_ip, None)
        if hostname is not None:
            self._increaseStats("hostname_cache")
        elif threaded:
            self.queue.put(["hostname", ip])
            return None
        else:
            hostname = self._resolveHostnameData(ip)

        return hostname["data"]

    def _resolveHostnameData(self, ip):
        _ip = ip.compressed
        hostname = self.hostname_map.get(_ip, None)
        if hostname is None:
            self._increaseStats("hostname_fetch")
            _hostname = socket.getfqdn(_ip)
            if _hostname != _ip:
                if not self.isExternal(ip):
                    _hostname = _hostname.split('.', 1)[0]
            elif type(ip) is ipaddress.IPv6Address and not self.isExternal(ip):
                # don't cache internal IPv6 Addresses, because they can get a dns name soon
                return { "data": _hostname, "time": time.time() }
            hostname = { "data": _hostname, "time": time.time() }
            with self.hostname_lock:
                self.hostname_map[_ip] = hostname
        else:
            self._increaseStats("hostname_cache")
        return hostname

    def getStateMetrics(self):
        return [
            "system_service_process{{type=\"ip_cache\",}} {}".format("1" if self.is_running else "0"),
            "system_service_state{{type=\"ip_cache_ip2location\",}} {}".format("1" if self.ip2location_state else "0"),
            "system_service_state{{type=\"ip_cache_dump\",}} {}".format("1" if self.valid_cache_file else "0")
        ]
