import socket
import pyinotify
import os
import sys
import signal
import traceback 
import logging

from datetime import datetime, timezone

sys.path.insert(0, "/opt/shared/python")

from smartserver.filewatcher import FileWatcher

class ShutdownException(Exception):
    pass

class Server():
    def initLogger(level):
        #journal.JournalHandler(SYSLOG_IDENTIFIER="pulp-sync")
        handler = logging.StreamHandler(sys.stdout)
        is_daemon = not os.isatty(sys.stdin.fileno())
        logging.basicConfig(
            handlers = [handler],
            level=level,
            format= "[%(levelname)s] - %(module)s - %(message)s" if is_daemon else "%(asctime)s - [%(levelname)s] - %(module)s - %(message)s",
            datefmt="%d.%m.%Y %H:%M:%S"
        )

    def __init__(self,name):
        self.filewatcher = None

        def shutdown(signum, frame):
            logging.info("Shutdown initiated")
            self.terminate()
            
        def exceptionHandler(type, value, tb):
            logger = logging.getLogger()
            logger.error("Uncaught exception: {0}".format(str(value)))
            for line in traceback.TracebackException(type, value, tb).format(chain=True):
                rows = line.split("\n")
                for row in rows:
                    if row == "":
                        continue
                    logger.error(row)

        signal.signal(signal.SIGTERM, shutdown)
        signal.signal(signal.SIGINT, shutdown)
        sys.excepthook = exceptionHandler

        self._lock_socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        try:
            # The null byte (\0) means the socket is created 
            # in the abstract namespace instead of being created 
            # on the file system itself.
            # Works only in Linux
            self._lock_socket.bind("\0{}".format(name))
        except socket.error:
            raise Exception("Service '{}' already running".format(name))

    def start(self, callback):
        try:
            callback()
        except ShutdownException as e:
            pass
        except Exception as e:
            logging.error(traceback.format_exc())

        logging.info("Stopped")

    def terminate(self):
        if self.filewatcher is not None:
            self.filewatcher.terminate()
        raise ShutdownException()
          
    def initWatchedFiles(self, watched_data_files, callback = None ):
        if watched_data_files is not None and len(watched_data_files) > 0:
            self.filewatcher = FileWatcher( logging, callback )
            
            self.watched_data_files = {}
            for watched_data_file in watched_data_files:
                self.filewatcher.addWatcher(watched_data_file)
                self.watched_data_files[watched_data_file] = self.filewatcher.getModifiedTime(watched_data_file)
                
    def getFileModificationTime(self,watched_data_file):
        return self.filewatcher.getModifiedTime(watched_data_file) if self.watched_data_files[watched_data_file] is not None else 0

    def hasFileChanged(self,watched_data_file):
        return ( self.watched_data_files[watched_data_file] != self.filewatcher.getModifiedTime(watched_data_file) ) if self.watched_data_files[watched_data_file] is not None else False

    def confirmFileChanged(self,watched_data_file):
        self.watched_data_files[watched_data_file] = self.filewatcher.getModifiedTime(watched_data_file)
        
