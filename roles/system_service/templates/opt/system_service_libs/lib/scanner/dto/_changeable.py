import inspect


class Changeable():
    UNCHANGED = 0
    CHANGED = 2
    NEW = 3
    DELETED = 4
    
    def __init__(self, cache, locked = False):
        self.is_created = True
        self.is_changed_raw = []
        self.is_changed_details = []
        
        self.details = {}
        
        self.cache = cache
        
        self._lock = locked
        self._lock_owner = None
        
        self.priorized_data = {}
        self.priorized_value = {}

    def _initPriorizedData(self, data):
        for _data in data:
            key = _data["key"]
            self.priorized_data[key] = {}
            self.priorized_value[key] = None
            if "source" in _data:
                self.priorized_data[key][_data["source"]] = {"value": _data["value"], "priority": _data["priority"]}
                self.priorized_value[key] = _data["value"]
            
    def _getPriorizedValue(self, key):
        return self.priorized_value[key]
    
    def _hasPriorizedData(self, key, source):
        return source in self.priorized_data[key]
        
    def _setPriorizedData(self, key, source, priority, value):
        if source not in self.priorized_data[key] or self.priorized_data[key][source]["priority"] != priority or self.priorized_data[key][source]["value"] != value:
            self.priorized_data[key][source] = {"value": value, "priority": priority}
            _priority = priority
            _value = value
            for data in self.priorized_data[key].values():
                if data["priority"] > _priority:
                    _priority = data["priority"]
                    _value = data["value"]
            if self.priorized_value[key] != _value:
                self.priorized_value[key] = _value
                self._markAsChanged("{}".format(key), "{}{}".format("change " if len(self.priorized_data[key].values()) > 1 else "set ", key))
            else:
                self._markAsChanged("_{}".format(key), "add {}".format(key))
    
    def _removePriorizedData(self, key, source):
        if source in self.priorized_data[key]:
            del self.priorized_data[key][source]
            _priority = 0
            _value = None
            for data in self.priorized_data[key].values():
                if data["priority"] > _priority:
                    _priority = data["priority"]
                    _value = data["value"]
            if self.priorized_value[key] != _value:
                self.priorized_value[key] = _value
                self._markAsChanged("{}".format(key), "{}{}".format("remove " if len(self.priorized_data[key].values()) > 0 else "clear ", key))
            else:
                self._markAsChanged("_{}".format(key), "remove {}".format(key))

    def getDetail(self, key, fallback = None):
        return self.details[key]["value"] if key in self.details else fallback

    def setDetail(self, key, value, fmt):
        self._checkLock()
        if key not in self.details or self.details[key]["value"] != value:
            self._markAsChanged(key, "{}{}".format( "add " if key not in self.details else "", key))
            self.details[key] = { "value": value, "format": fmt }
            return True
        return False
        
    def removeDetail(self, key):
        self._checkLock()
        if key in self.details:
            self._markAsChanged(key, "remove {}".format(key))
            del self.details[key]

    def _getDetails(self):
        return self.details

    def _getCache(self):
        return self.cache

    def _markAsChanged(self, type, details = None):
        self.is_changed_raw.append(type)
        self.is_changed_details.append( details if details else type)

    def _getModificationState(self):
        if self.is_created:
            return Changeable.NEW
        if len(self.is_changed_raw) > 0:
            return Changeable.CHANGED
        return Changeable.UNCHANGED
        
    def confirmModificationState(self):
        state = self._getModificationState()
        changed_raw = self.is_changed_raw;
        changed_details = self.is_changed_details;
        
        self.is_created = False
        self.is_changed_raw = []
        self.is_changed_details = []
        
        changed_details = list(set(changed_details))
        changed_details.sort()
        return [state, list(set(changed_raw)), ", ".join(changed_details)]
    
    def _checkLock(self):
        if not self._lock:
            raise Exception("Not locked " + str(self) )
        
    def isLocked(self):
        return self._lock

    def lock(self, owner):
        #print("lock " + str(self))

        if self._lock:
            #[_, file ] = self._last_lock_source[1].rsplit("/", 1)
            #last_log_source_msg = "{}.{}:{}".format( file[:-3] , self._last_lock_source[3], self._last_lock_source[2])
            #raise Exception("Still locked " + str(self) + " in " + last_log_source_msg )
            raise Exception("{} still locked".format(str(self)) )
        
        if self._lock_owner is not None and self._lock_owner != owner:
            raise Exception("Lock of {} owned by {}".format(str(self), str(self._lock_owner)) )
        
        self._lock = True
        self._lock_owner = owner
        #self._last_lock_source = inspect.stack()[2]

    def unlock(self, owner):
        if not self._lock:
            raise Exception("Unable to unlock " + str(self) )
        
        if self._lock_owner != owner:
            raise Exception("Lock of {} owned by {}".format(str(self), str(self._lock_owner)) )

        #print("unlock " + str(self))
        self._lock = False
        self._lock_owner = None
