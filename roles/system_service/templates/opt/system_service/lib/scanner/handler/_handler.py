from datetime import datetime, timedelta
import logging
import threading
import time
import traceback

import json

from smartserver.metric import Metric

from lib.scanner.dto.event import Event
from lib.scanner.helper import Helper


class Handler:
    def __init__(self, config, cache, with_worker = True):
        self.config = config
        self.cache = cache

        self.dispatcher = None
        
        self.is_suspended = {}

        self.is_running = False

        if with_worker:
            self.event = threading.Event()
            self.thread = threading.Thread(target=self.run, args=())
        else:
            self.event = None
            self.thread = None

        self.device_metric_states = {}
        self.service_metric_states = {}

    def getStateMetrics(self):
        metrics = []
        for hostname in self.device_metric_states:
            metrics.append(Metric.buildStateMetric("system_service", self.__class__.__name__.lower(), "device", self.device_metric_states[hostname], { "hostname": hostname }))

        for service in self.service_metric_states:
            metrics.append(Metric.buildStateMetric("system_service", service, "connection", self.service_metric_states[service]))

        if self.thread is not None:
            metrics.append(Metric.buildProcessMetric("system_service", "scanner.{}".format(self.__class__.__name__.lower()), "1" if self.is_running else "0"))
        return metrics

    def _setDeviceMetricState(self, hostname, value):
        self.device_metric_states[hostname] = value

    def _setServiceMetricState(self, service, value):
        self.service_metric_states[service] = value

    def start(self):
        if self.thread is not None:
            self.is_running = True
            self.thread.start()

    def run(self):
        try:
            logging.info("{} started".format(self.__class__.__name__.lower().title()))
            self._run()
        except Exception as e:
            self.is_running = False
            raise e
        finally:
            logging.info("{} stopped".format(self.__class__.__name__.lower().title()))

    def terminate(self):
        if self.event is not None:
            #logging.info("Shutdown {}".format(self.__class__.__name__.lower()))
            self.is_running = False
            self.event.set()
            self.thread.join()
        
    def _wait(self, timeout):
        #logging.info("wait {}".format(self.__class__.__name__))
        if self.event is not None:
            self.event.wait(timeout)
            self.event.clear()
        
    def _wakeup(self):
        if self.event is not None:
            self.event.set()
        
    def _isRunning(self):
        return self.is_running
    
    def _isSuspended(self, key = None):
        return self._getSuspendTimeout(key) > 0
        
    def _getSuspendTimeout(self, key = None):
        suspend_data = self.is_suspended.get(key, None)
        if suspend_data is not None:
            suspend_time = (datetime.now() - suspend_data[0]).total_seconds()
            if suspend_time > suspend_data[1]:
                Helper.logInfo("Resume {}{}".format(self.__class__.__name__, " {}".format(key) if key is not None else ""), 2)
                self.is_suspended[key] = None
            else:
                return suspend_data[1] - suspend_time
        return 0
        
    def _handleExpectedException(self, msg, key, timeout = 60):
        Helper.logInfo("{}.{}".format(msg, " Will suspend{} for {}.".format(" {}".format(key) if key is not None else "", timedelta(seconds=timeout) if timeout >= 0 else "")), 2)
        self.is_suspended[key] = [datetime.now(), timeout]
    
    def _handleUnexpectedException(self, e, key = None, timeout = 900):
        Helper.logError("{} got unexpected exception.{}".format(self.__class__.__name__, " Will suspend{} for {} minute(s).".format(" {}".format(key) if key is not None else "", timeout / 60) if timeout >= 0 else ""), 2)
        Helper.logError(traceback.format_exc(), 2)
        self.is_suspended[key] = [datetime.now(), timeout]
        
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
