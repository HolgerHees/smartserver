import os
import threading
import logging
import sys

from datetime import datetime

from smartserver import inotify


class FileWatcher():
    EVENT_TYPE_DELETED = "deleted"
    EVENT_TYPE_CREATED = "created"
    EVENT_TYPE_WRITTEN = "written"
    EVENT_TYPE_MOVED_TO = "moved_to"
    EVENT_TYPE_MOVED_FROM = "moved_from"

    def __init__(self, callback = None):
        super().__init__()
        
        self.callback = callback

        self.modified_time = {}

        self.watched_parents = {}

        self.inotify = inotify.INotify(self.inotifyEvent)

        self.inotify_lock = threading.Lock()
        self.inotify_in_progress = {}

    def notifyListener(self, event):
        if self.callback:
            #logging.info("Notify listener of '{}'".format(event))
            self.callback(event)

    def inotifyDummyEvent(self, event):
        with self.inotify_lock:
            if event.path not in self.inotify_in_progress:
                return
            del self.inotify_in_progress[event.path]

        self.inotifyEvent(inotify.INotifyEvent(event.wd, ( event.mask | inotify.Constants.IN_CLOSE_WRITE ) ^ inotify.Constants.IN_CREATE, event.cookie, event.name, event.wd_path))

    def inotifyEvent(self, event):
        #logging.info("{}".format(event))

        if event.path not in self.modified_time and event.wd_path not in self.modified_time:
            #logging.info("Skipped unrelated parent watch")
            return

        if event.mask & inotify.Constants.IN_MOVED_FROM:
            if event.path in self.modified_time:
                #logging.info("Deleted path '{}'".format(event.path))
                self.removePath(event.path)
            self.notifyListener({"path": event.path, "type": FileWatcher.EVENT_TYPE_MOVED_FROM, "time": datetime.now().timestamp()})

        elif event.mask & inotify.Constants.IN_MOVED_TO:
            if event.path in self.modified_time:
                #logging.info("New path '{}'".format(event.path))
                self.addPath(event.path)
            self.notifyListener({"path": event.path, "type": FileWatcher.EVENT_TYPE_MOVED_TO, "time": datetime.now().timestamp()})

        elif event.mask & inotify.Constants.IN_CREATE:
            #logging.info("New path '{}'".format(event.path))
            if event.path in self.modified_time:
                self.addPath(event.path)

            self.notifyListener({"path": event.path, "type": FileWatcher.EVENT_TYPE_CREATED, "time": datetime.now().timestamp()})

            #logging.info(os.stat(event.path))

            #if os.stat(event.path).st_nlink > 1:
            #    self.notifyListener({"path": event.path, "type": FileWatcher.EVENT_TYPE_WRITTEN, "time": datetime.now().timestamp()})
            if not (event.mask & inotify.Constants.IN_ISDIR):
                self.inotify_in_progress[event.path] = threading.Timer(5, self.inotifyDummyEvent, [event, ] )
                self.inotify_in_progress[event.path].start()

        elif event.mask & inotify.Constants.IN_OPEN:
            with self.inotify_lock:
                if event.path not in self.inotify_in_progress:
                    return
                self.inotify_in_progress[event.path].cancel()
                del self.inotify_in_progress[event.path]

        elif event.mask & inotify.Constants.IN_CLOSE_WRITE:
            if event.path in self.inotify_in_progress: # can happen when IN_CREATE instead of IN_OPEN was called
                with self.inotify_lock:
                    if event.path in self.inotify_in_progress:
                        self.inotify_in_progress[event.path].cancel()
                        del self.inotify_in_progress[event.path]

            #logging.info("Closed path '{}'".format(event.path))
            if event.path in self.modified_time:
                self.modified_time[event.path] = datetime.now().timestamp()
            self.notifyListener({"path": event.path, "type": FileWatcher.EVENT_TYPE_WRITTEN, "time": datetime.now().timestamp()})

        elif event.mask & inotify.Constants.IN_DELETE:
            #logging.info("Deleted path '{}'".format(event.path))
            if event.path in self.modified_time:
                self.removePath(event.path)
            self.notifyListener({"path": event.path, "type": FileWatcher.EVENT_TYPE_DELETED, "time": datetime.now().timestamp()})

        else:
            logging.error("Ignored event {}".format(event))

    def addWatcher(self,path):
        path = path.rstrip("/")

        parent = os.path.dirname(path)
        if parent not in self.watched_parents:
            self.watched_parents[parent] = True
            #self.inotify.add_watch(parent, inotify.Constants.IN_OPEN | inotify.Constants.IN_CLOSE_WRITE | inotify.Constants.IN_CLOSE_NOWRITE | inotify.Constants.IN_CREATE | inotify.Constants.IN_MOVED_FROM | inotify.Constants.IN_MOVED_TO | inotify.Constants.IN_DELETE )
            self.inotify.add_watch(parent, inotify.Constants.IN_OPEN | inotify.Constants.IN_CLOSE_WRITE | inotify.Constants.IN_CREATE | inotify.Constants.IN_MOVED_FROM | inotify.Constants.IN_MOVED_TO | inotify.Constants.IN_DELETE )

        if os.path.exists(path):
            self.addPath(path)
        else:
            self.modified_time[path] = 0
            
    def addPath(self, path):
        #logging.info("addPath " + path)

        self.modified_time[path] = os.stat(path).st_mtime

        if os.path.isdir(path):
            self.inotify.add_watch(path, inotify.Constants.IN_OPEN | inotify.Constants.IN_CLOSE_WRITE | inotify.Constants.IN_CREATE | inotify.Constants.IN_MOVED_FROM | inotify.Constants.IN_MOVED_TO | inotify.Constants.IN_DELETE )

    def removePath(self, path):
        #logging.info("removePath " + path)

        self.modified_time[path] = 0

        if os.path.isdir(path):
            self.inotify.rm_watch(path)

    def getModifiedTime(self,path):
        return self.modified_time[path.rstrip("/")]
      
    def start(self):
        self.inotify.start()

    def terminate(self):
        if self.inotify.is_alive():
            self.inotify.stop()
            self.inotify.join()
