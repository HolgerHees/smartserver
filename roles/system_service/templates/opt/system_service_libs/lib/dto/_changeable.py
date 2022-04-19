import inspect


class Changeable():
    UNCHANGED = 0
    CHANGED = 2
    NEW = 3
    DELETED = 4
    
    def __init__(self):
        self.is_created = True
        self.is_changed_raw = []
        self.is_changed_details = []
        
        self._lock = False
        
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
        return [state, changed_raw, ", ".join(changed_details)]
        
    def lock(self):
        #print("lock " + str(self))

        if self._lock:
            #[_, file ] = self._last_lock_source[1].rsplit("/", 1)
            #last_log_source_msg = "{}.{}:{}".format( file[:-3] , self._last_lock_source[3], self._last_lock_source[2])
            #raise Exception("Still locked " + str(self) + " in " + last_log_source_msg )
            raise Exception("Still locked " + str(self) )
        
        self._lock = True
        self._last_lock_source = inspect.stack()[2]

    def unlock(self):
        #print("unlock " + str(self))
        self._lock = False



