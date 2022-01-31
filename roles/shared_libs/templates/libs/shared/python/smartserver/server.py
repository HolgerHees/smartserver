import socket
import pyinotify
import os

from datetime import datetime, timezone


class Identity(pyinotify.ProcessEvent):
    def __init__(self, s):
        super().__init__(s)
        self.modified_time = {}
        
    def process_default(self, event):
        self.modified_time[event.path] = datetime.timestamp(datetime.now())
        
    def addWatcher(self,path,wm):
        file_stat = os.stat(path)
        self.modified_time[path] = file_stat.st_mtime
        wm.add_watch(path, pyinotify.IN_DELETE_SELF | pyinotify.IN_CLOSE_WRITE | pyinotify.IN_MODIFY, rec=True, auto_add=True)
        
    def getModifiedTime(self,path):
        return self.modified_time[path]

# Thread #1

class Server():
    def __init__(self,name,watched_data_files):
      
        self._lock_socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        try:
            # The null byte (\0) means the socket is created 
            # in the abstract namespace instead of being created 
            # on the file system itself.
            # Works only in Linux
            self._lock_socket.bind("\0{}".format(name))
        except socket.error:
            return
        
        wm = pyinotify.WatchManager()
        s = pyinotify.Stats()
        self.identity = Identity(s)
        notifier = pyinotify.ThreadedNotifier(wm, default_proc_fun=self.identity)
        notifier.start()
        
        self.watched_data_files = {}
        for watched_data_file in watched_data_files:
            if not os.path.isfile(watched_data_file):
                self.watched_data_files[watched_data_file] = None
            else:
                self.identity.addWatcher(watched_data_file,wm)
                self.watched_data_files[watched_data_file] = self.identity.getModifiedTime(watched_data_file)
                
    def getFileModificationTime(self,watched_data_file):
        return self.identity.getModifiedTime(watched_data_file) if self.watched_data_files[watched_data_file] is not None else 0

    def hasFileChanged(self,watched_data_file):
        return ( self.watched_data_files[watched_data_file] != self.identity.getModifiedTime(watched_data_file) ) if self.watched_data_files[watched_data_file] is not None else False

    def confirmFileChanged(self,watched_data_file):
        self.watched_data_files[watched_data_file] = self.identity.getModifiedTime(watched_data_file)
