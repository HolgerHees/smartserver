import pyinotify
import os
import threading
import logging

from datetime import datetime

class FileWatcher(pyinotify.ProcessEvent):
    def __init__(self, callback = None):
        super().__init__(pyinotify.Stats())
        
        self.is_running = True

        self.callback = callback

        wm = pyinotify.WatchManager()
        self.notifier = pyinotify.ThreadedNotifier(wm, default_proc_fun=self)
        #self.notifier.daemon = True
        self.notifier.start()

        self.wm = wm
        
        self.modified_time = {}

        self.watched_files = {}
        self.watched_parents = {}
        
        self.watched_directories = {}
        
    def notifyListener(self, event):
        if self.callback:
            #logging.info("Notify listener of '{}' - '{}'".format(event["path"],event["maskname"]))
            self.callback(event)

    def process_default(self, event):
        #logging.info(event)

        if event.path in self.watched_parents:
            if event.mask & pyinotify.IN_DELETE:
                pass
            elif event.mask & ( pyinotify.IN_CREATE | pyinotify.IN_MOVED_TO | pyinotify.IN_MOVED_FROM ):
                if event.pathname in self.modified_time:
                    logging.info("New path '{}' watched".format(event.pathname))
                    self.addPath(event.pathname)
                    if not event.dir:
                        self.notifyListener({"path": event.pathname, "pathname": event.pathname, "mask": pyinotify.IN_CLOSE_WRITE, "maskname": "IN_CLOSE_WRITE", "time": datetime.now().timestamp(), "cookie": event.cookie if hasattr(event,"cookie") else None })

        elif event.path in self.watched_directories:
            now = datetime.now().timestamp()
            self.modified_time[event.path] = now
            notifier_event = {"path": event.path, "pathname": event.pathname, "mask": event.mask, "maskname": event.maskname, "time": now, "cookie": event.cookie if hasattr(event,"cookie") else None }
            self.notifyListener(notifier_event)
        elif event.path in self.watched_files:
            if event.mask & ( pyinotify.IN_DELETE_SELF | pyinotify.IN_IGNORED ):
                pass
            elif event.mask & pyinotify.IN_CLOSE_WRITE:
                now = datetime.now().timestamp()
                self.modified_time[event.path] = now
                self.notifyListener({"path": event.path, "pathname": event.pathname, "mask": event.mask, "maskname": event.maskname, "time": now, "cookie": event.cookie if hasattr(event,"cookie") else None })
            else:
                logging.error("Ignored event {}".format(event))
                pass
        
    def addWatcher(self,path):
        path = path.rstrip("/")

        parent = os.path.dirname(path)
        if parent not in self.watched_parents:
            self.watched_parents[parent] = True
            self.wm.add_watch(parent, pyinotify.IN_CREATE | pyinotify.IN_DELETE | pyinotify.IN_MOVED_TO | pyinotify.IN_MOVED_FROM, rec=False, auto_add=False)
            
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
            self.wm.add_watch(path, pyinotify.IN_CREATE | pyinotify.IN_DELETE | pyinotify.IN_CLOSE_WRITE | pyinotify.IN_MOVED_TO | pyinotify.IN_MOVED_FROM, rec=False, auto_add=False)

    def getModifiedTime(self,path):
        return self.modified_time[path.rstrip("/")]
      
    def terminate(self):
        self.is_running = False
        self.notifier.stop()
