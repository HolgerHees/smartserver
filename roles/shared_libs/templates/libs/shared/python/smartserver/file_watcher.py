import pyinotify
import os
from datetime import datetime

class FileWatcher(pyinotify.ProcessEvent):
    def __init__(self, callback = None):
        super().__init__(pyinotify.Stats())
        
        self.callback = callback

        wm = pyinotify.WatchManager()
        notifier = pyinotify.ThreadedNotifier(wm, default_proc_fun=self)
        notifier.start()

        self.wm = wm
        
        self.modified_time = {}

        self.watched_files = {}
        self.watched_parents = {}
        
        self.watched_directories = {}

    def process_default(self, event):
        if event.path in self.watched_directories:
            self.modified_time[event.path] = datetime.timestamp(datetime.now())
            if self.callback:
                self.callback(event)
      
        if event.path in self.watched_parents:
            if event.pathname in self.watched_files:
                self.addWatcher(event.pathname)
                if self.callback:
                    self.callback(event)
        else:
            if event.maskname == "IN_DELETE_SELF":
                #del self.watched_files[event.path]
                pass
            else:
                self.modified_time[event.path] = datetime.timestamp(datetime.now())
                if self.callback:
                    self.callback(event)
        
    def addWatcher(self,path):
        file_stat = os.stat(path)
        self.modified_time[path] = file_stat.st_mtime
        if os.path.isdir(path):
            self.watched_directories[path] = True
            self.wm.add_watch(path, pyinotify.IN_CREATE | pyinotify.IN_DELETE, rec=True, auto_add=True)
        else:
            self.watched_files[path] = True
            #self.wm.add_watch(path, pyinotify.IN_DELETE_SELF | pyinotify.IN_CLOSE_WRITE | pyinotify.IN_MODIFY, rec=False, auto_add=True)
            self.wm.add_watch(path, pyinotify.IN_DELETE_SELF | pyinotify.IN_CLOSE_WRITE, rec=False, auto_add=True)
            
            parent = os.path.dirname(path)
            if parent not in self.watched_parents:
                self.watched_parents[parent] = True
                self.wm.add_watch(parent, pyinotify.IN_CREATE | pyinotify.IN_MOVED_TO, rec=False, auto_add=True)
            
    def getModifiedTime(self,path):
        return self.modified_time[path]
