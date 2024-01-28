import socket
import pyinotify
import os
import sys
import signal
import traceback 
import logging
import threading

from flask import Flask, request
from flask_socketio import SocketIO
from werkzeug.serving import WSGIRequestHandler

from datetime import datetime, timezone

from smartserver.filewatcher import FileWatcher


serverWeb = Flask(__name__)
serverWeb.logger = logging.getLogger()
#app.config['SECRET_KEY'] = 'test!'
#socketio = SocketIO(app, async_mode="threading", logger=logging.getLogger(), cors_allowed_origins="*")
serverSocket = SocketIO(serverWeb, async_mode="threading", cors_allowed_origins="*")

class ShutdownException(Exception):
    pass

class CustomFormatter(logging.Formatter):
    def __init__(self, fmt):
        super().__init__()
        self.fmt = fmt

    def format(self, record):
        if "custom_module" not in record.__dict__:
            module = record.pathname.replace("/",".")[:-3] + ":" + str(record.lineno)
            module = module.ljust(25)
            module = module[-25:]
            
            record.__dict__["custom_module"] = module
            
        formatter = logging.Formatter(self.fmt)
        return formatter.format(record)
            
class Server():
    def initLogger(level):
        is_daemon = not os.isatty(sys.stdin.fileno())

        #journal.JournalHandler(SYSLOG_IDENTIFIER="pulp-sync")
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(CustomFormatter(
            "[%(levelname)s] - [%(custom_module)s] - %(message)s" if is_daemon else "%(asctime)s - [%(levelname)s] - [%(custom_module)s] - %(message)s"
            #"[%(levelname)s] - %(module).12s:%(lineno)d - %(message)s" if is_daemon else "%(asctime)s - [%(levelname)s] - %(module)s:%(lineno)d - %(message)s",
        ))
        
        logging.basicConfig(
            handlers = [handler],
            level=level,
            #format= CustomFormatter("[%(levelname)s] - %(module)s - %(message)s" if is_daemon else "%(asctime)s - [%(levelname)s] - %(module)s - %(message)s"),
            datefmt="%d.%m.%Y %H:%M:%S"
        )

    def __init__(self, name, ip, port):
        self.ip = ip
        self.port = port

        self.filewatcher = None

        def shutdown(signum, frame):
            self.terminate()
            
        signal.signal(signal.SIGTERM, shutdown)
        signal.signal(signal.SIGINT, shutdown)
        sys.excepthook = self._exceptionHandler

        self.thread_debugger = {}
        self._installThreadExcepthook()

        self._lock_socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        try:
            # The null byte (\0) means the socket is created 
            # in the abstract namespace instead of being created 
            # on the file system itself.
            # Works only in Linux
            self._lock_socket.bind("\0{}".format(name))
        except socket.error:
            raise Exception("Service '{}' already running".format(name))

    def _installThreadExcepthook(self):
        _init = threading.Thread.__init__
        _self = self

        def init(self, *args, **kwargs):
            _init(self, *args, **kwargs)
            _run = self.run

            def run(*args, **kwargs):
                _self.thread_debugger[self.name] = str(_run)
                try:
                    _run(*args, **kwargs)
                except:
                    sys.excepthook(*sys.exc_info())
                del _self.thread_debugger[self.name]
            self.run = run

        threading.Thread.__init__ = init

    def _exceptionHandler(self, type, value, tb):
        logger = logging.getLogger()
        logger.error("Uncaught exception: {0}".format(str(value)))
        for line in traceback.TracebackException(type, value, tb).format(chain=True):
            rows = line.split("\n")
            for row in rows:
                if row == "":
                    continue
                logger.error(row)

    def start(self):
        try:
            WSGIRequestHandler.protocol_version = "HTTP/1.1"
            serverSocket.run(app=serverWeb, use_reloader=False, host=self.ip, port=self.port, allow_unsafe_werkzeug=True)
            #app.run(debug=False, use_reloader=False, threaded=True, host="0.0.0.0", port='80')
        except ShutdownException as e:
            pass
        except Exception as e:
            logging.error(traceback.format_exc())

        for thread in threading.enumerate():
            if thread.name == "MainThread":
                continue
            logging.warning("Thread '{}' is still running: {}".format(thread.name, self.thread_debugger[thread.name]))

        logging.info("Server stopped")

    def terminate(self):
        logging.info("Shutdown server")

        if self.filewatcher is not None:
            self.filewatcher.terminate()
        raise ShutdownException()

    def getRequestHeader(self, field):
        return request.headers[field] if field in request.headers else None

    def getRequestValue(self, field):
        return request.form[field] if field in request.form else None

    def getRequestValues(self, field):
        return request.form

    def emitSocketData(self, topic, data):
        with serverWeb.app_context():
            return serverSocket.emit(topic, data)

    def initWatchedFiles(self, watched_data_files, callback = None ):
        if watched_data_files is not None and len(watched_data_files) > 0:
            self.filewatcher = FileWatcher( callback )
            
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

@serverSocket.on_error_default
def on_error(e):
    logging.error(e)
    sys.excepthook(*sys.exc_info())

@serverSocket.on('connect')
def on_connect():
    logging.info("on_connect {}".format(request.sid))

@serverSocket.on('disconnect')
def on_disconnect():
    logging.info("on_disconnect {}".format(request.sid))

Server.initLogger(logging.INFO)

