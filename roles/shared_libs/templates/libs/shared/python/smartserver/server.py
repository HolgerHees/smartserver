import socket
import pyinotify
import os
import sys

from datetime import datetime, timezone

sys.path.insert(0, "/opt/shared/python")

from smartserver.file_watcher import FileWatcher

class Server():
    def __init__(self,name, watched_data_files = None, callback = None):
        self._lock_socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        try:
            # The null byte (\0) means the socket is created 
            # in the abstract namespace instead of being created 
            # on the file system itself.
            # Works only in Linux
            self._lock_socket.bind("\0{}".format(name))
        except socket.error:
            return
          
        if watched_data_files is not None and len(watched_data_files) > 0:
            self.filewatcher = FileWatcher( callback )
            
            self.watched_data_files = {}
            for watched_data_file in watched_data_files:
                if not os.path.exists(watched_data_file):
                    self.watched_data_files[watched_data_file] = None
                else:
                    self.filewatcher.addWatcher(watched_data_file)
                    self.watched_data_files[watched_data_file] = self.filewatcher.getModifiedTime(watched_data_file)
                
    def getFileModificationTime(self,watched_data_file):
        return self.filewatcher.getModifiedTime(watched_data_file) if self.watched_data_files[watched_data_file] is not None else 0

    def hasFileChanged(self,watched_data_file):
        return ( self.watched_data_files[watched_data_file] != self.filewatcher.getModifiedTime(watched_data_file) ) if self.watched_data_files[watched_data_file] is not None else False

    def confirmFileChanged(self,watched_data_file):
        self.watched_data_files[watched_data_file] = self.filewatcher.getModifiedTime(watched_data_file)
