from datetime import datetime
import logging
import threading
import time

import json

from lib.dto.event import Event


class Handler:
    def __init__(self, with_worker = True):
        self.dispatcher = None
        
        self.is_suspended = {}

        self.is_running = with_worker

        if with_worker:
            self.event = threading.Event()
            self.thread = threading.Thread(target=self._run, args=())
        else:
            self.event = None
            self.thread = None
        
    def start(self):
        if self.thread is not None:
            self.thread.start()

    def terminate(self):
        if self.event is not None:
            self.is_running = False
            self.event.set()
        
    def _wait(self, timeout):
        #logging.info("wait {}".format(self.__class__.__name__))
        if self.event is not None:
            self.event.wait(timeout)
            self.event.clear()
        
    def _sleep(self, timeout):
        time.sleep(timeout)
        
    def _wakeup(self):
        if self.event is not None:
            self.event.set()
        
    def _isRunning(self):
        return self.is_running
    
    def _suspend(self, key = None):
        self.is_suspended[key] = True
        
    def _isSuspended(self, key = None):
        return self.is_suspended.get(key, False)
    
    def _confirmSuspended(self, key = None):
        logging.warning("Resume {}".format(self.__class__.__name__))
        self.is_suspended[key] = False
    
    def _handleUnexpectedException(self, e, key = None):
        logging.error("{} got unexpected exception. Will suspend for 15 minutes.".format(self.__class__.__name__))
        logging.error(traceback.format_exc())
        self.is_suspended[key] = True
        return 900
        
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
    
    def getEventTypes(self):
        return []
    
    def processEvents(self, events):
        pass
