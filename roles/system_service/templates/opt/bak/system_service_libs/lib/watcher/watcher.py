import time
from datetime import datetime

import json

from lib.dto.event import Event


class Watcher:
    def __init__(self, logger):
        self.logger = logger
        
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

    def triggerEvents(self, groups, devices, stats, events):
        pass

    def processEvents(self, groups, devices, stats, events):
        pass

    def _appendChange(self, changes, type, identifier, additional_payload ):
        if type not in changes:
            changes[type] = []
            
        changes[type].append( [ identifier, additional_payload ] )
        
    def _prepareEvents(self, changes):
        events = []
        for event_type in changes:
            identifiers = {}
            for [ identifier, additional_payload ] in changes[event_type]:
                if identifier not in identifiers:
                    identifiers[identifier] = {}

                for pid in additional_payload:
                    identifiers[identifier][pid] = additional_payload[pid]
                        
            for identifier in identifiers:
                events.append(Event(event_type, identifier, identifiers[identifier]))
        return events
