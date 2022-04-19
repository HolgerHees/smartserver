import time
from datetime import datetime

import json

from lib.dto.event import Event


class Handler:
    def __init__(self):
        self.dispatcher = None
    
    def setDispatcher(self, dispatcher):
        self.dispatcher = dispatcher
        
    def _getDispatcher(self):
        return self.dispatcher
        
    def getStartupTimestamp(self):
        return round(self.getNowAsTimestamp() - 0.1,3)

    def getNowAsTimestamp(self):
        return round(datetime.now().timestamp(),3)
    
    def data_equal(self, d1, d2):
        if type(d1) != type(d2):
            return False

        if isinstance(d1, dict) or isinstance(d1, list):
            if len(d1) != len(d2):
                return False

            if isinstance(d1, dict):
                for key in d1:
                    if key not in d2:
                        return False
                    
                    result = self.data_equal(d1[key], d2[key])
                    if not result:
                        return False
                
                for key in d2:
                    if key not in d1:
                        return False

            else:
                for value1 in d1:
                    is_equal = False
                    for value2 in d2:
                        if type(value1) != type(value2):
                            continue
                        result = self.data_equal(value1, value2)
                        if result:
                            is_equal = True
                            break
                    if not is_equal:
                        return False
            
        elif d1 != d2:
            return False
            
        return True
    
    def start(self):
        pass

    def terminate(self):
        pass
    
    def getEventTypes(self):
        return []
    
    def processEvents(self, events):
        pass
