import os
import json
import time
from datetime import datetime

class Watcher:
    def __init__(self, logger):
        self.logger = logger
        
    def getStartupTimestamp(self):
        return round(self.getNowAsTimestamp() - 0.1,3)

    def getNowAsTimestamp(self):
        return round(datetime.timestamp(datetime.now()),3)

    def readJsonFile(self,path,shouldRetry,default):
        return self._readJsonFile(path, 5 if shouldRetry else 0, default)
      
    def _readJsonFile(self,path,retries,default):
        try:
            if os.path.isfile(path):
                with open(path, 'r') as f:
                    return json.load(f)
            return default
        except json.decoder.JSONDecodeError as e:
            if retries > 0:
                time.sleep(0.1)
                retries -= 1
                self.logger.info("File was not ready. Retry {} in 100ms".format( 5 - retries))
                return self.readJsonFile(path,retries,default)
            raise e
