import pyinotify
import os
from datetime import datetime

class FileWatcher(pyinotify.ProcessEvent):
    def __init__(self, logger, callback = None):
        super().__init__(pyinotify.Stats())
        
        self.logger = logger
        
        self.callback = callback

        wm = pyinotify.WatchManager()
        self.notifier = pyinotify.ThreadedNotifier(wm, default_proc_fun=self)
        self.notifier.daemon = True
        self.notifier.start()

        self.wm = wm
        
        self.modified_time = {}

        self.watched_files = {}
        self.watched_parents = {}
        
        self.watched_directories = {}
        
    def notifyListener(self, event):
        if self.callback:
            self.logger.info("Notify listener of '{}' - '{}'".format(event["path"],event["maskname"]))
            self.callback(event)

    def process_default(self, event):
        #self.logger.info(event)
      
        if event.path in self.watched_parents:
            if event.mask & pyinotify.IN_DELETE:
                pass
            elif event.mask & ( pyinotify.IN_CREATE | pyinotify.IN_MOVED_TO ):
                if event.pathname in self.modified_time:
                    self.logger.info("New path '{}' watched".format(event.pathname))
                    self.addPath(event.pathname)
                    if not event.dir:
                        self.notifyListener({"path": event.pathname, "pathname": event.pathname, "mask": pyinotify.IN_CLOSE_WRITE, "maskname": "IN_CLOSE_WRITE" })

        elif event.path in self.watched_directories:
            if event.mask & ( pyinotify.IN_CREATE | pyinotify.IN_DELETE ):
                self.modified_time[event.path] = datetime.timestamp(datetime.now())
                self.notifyListener({"path": event.path, "pathname": event.pathname, "mask": event.mask, "maskname": event.maskname })
      
        elif event.path in self.watched_files:
            if event.mask & pyinotify.IN_CLOSE_WRITE:
                self.modified_time[event.path] = datetime.timestamp(datetime.now())
                self.notifyListener({"path": event.path, "pathname": event.pathname, "mask": event.mask, "maskname": event.maskname })
            else:
                pass
        
    def addWatcher(self,path):
        path = path.rstrip("/")

        parent = os.path.dirname(path)
        if parent not in self.watched_parents:
            self.watched_parents[parent] = True
            self.wm.add_watch(parent, pyinotify.IN_CREATE | pyinotify.IN_DELETE | pyinotify.IN_MOVED_TO, rec=False, auto_add=False)
            
        if os.path.exists(path):
            self.addPath(path)
        else:
            self.modified_time[path] = 0
            
    def addPath(self, path):
        #print("addPath " + path)

        file_stat = os.stat(path)
        self.modified_time[path] = file_stat.st_mtime

        isfile = os.path.isfile(path)
        if isfile:
            self.watched_files[path] = True
            self.wm.add_watch(path, pyinotify.IN_DELETE_SELF | pyinotify.IN_CLOSE_WRITE, rec=False, auto_add=False)
        else:
            self.watched_directories[path] = True
            self.wm.add_watch(path, pyinotify.IN_CREATE | pyinotify.IN_DELETE, rec=False, auto_add=False)
            
    def getModifiedTime(self,path):
        return self.modified_time[path.rstrip("/")]
      
    def terminate(self):
        self.notifier.stop()
