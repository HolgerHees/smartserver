import socket
import pyinotify
import os
import sys
import signal
import traceback 
import logging
import threading

from flask import Flask, request, Response
from flask_socketio import SocketIO, join_room, leave_room
from werkzeug.serving import WSGIRequestHandler, make_server

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
    serverHandler = None

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

        self.socket_clients = {}
        self.socket_rooms = {}

        self.filewatcher = None

        self.socket_watcher_timer = None

        self.socketio_emint_lock = threading.Lock()
        self.socketio_client_lock = threading.Lock()

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

            #logging.info("Thread '{}' started: {} => {} => {}".format(self.name, str(_run), str(_self), sys._getframe(1).f_code.co_name))

            def run(*args, **kwargs):
                _self.thread_debugger[self.name] = [ str(_run), str(_self) ]
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
            Server.serverHandler = self

            WSGIRequestHandler.protocol_version = "HTTP/1.1"
            _run_wsgi = WSGIRequestHandler.run_wsgi
            def run_wsgi(self) -> None:
                try:
                    _run_wsgi(self)
                except AssertionError as e:
                    # can happen on closed websocket connections
                    if str(e) == "write() before start_response" and self.environ["QUERY_STRING"].endswith("websocket"):
                        #if not self.connection._closed:
                        #    logging.warn("Skipped 'write() before start_response'")
                        return
                    raise e
            WSGIRequestHandler.run_wsgi = run_wsgi

            #logging.info("Server listen on http://{}:{}/".format(self.ip, self.port))
            #self.server = make_server(self.ip, self.port, serverWeb, threaded = True)
            #self.server.passthrough_errors = True
            #self.server.serve_forever()
            serverWeb.run(host=self.ip, port=self.port, use_reloader=False, threaded = True, passthrough_errors = True)

            #serverSocket.run(app=serverWeb, use_reloader=False, host=self.ip, port=self.port, allow_unsafe_werkzeug=True)
        except ShutdownException as e:
            pass
        except Exception as e:

            logging.error(traceback.format_exc())

        for thread in threading.enumerate():
            if thread.name == "MainThread":
                continue
            logging.warning("Thread '{}' is still running: {} => {}".format(thread.name, self.thread_debugger[thread.name][0], self.thread_debugger[thread.name][1]))

        logging.info("Server stopped")

    def terminate(self):
        logging.info("Server shutdown")

        if self.filewatcher is not None:
            self.filewatcher.terminate()
        raise ShutdownException()

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

    def getRequestHeader(self, field):
        return request.headers[field] if field in request.headers else None

    def getRequestValue(self, field):
        return request.form[field] if field in request.form else None

    #def getRequestValues(self, field):
    #    return request.form

    def buildStatusResult(self, code, message):
        return {
            "code": code,
            "message": message
        }

    def getSocketParamValue(self, params, field):
        return params[field] if field in params else None

    def _socketWatcherInfo(self):
        self.socket_watcher_timer = None
        logging.info("Websocket: {} client(s) and {} room(s) active".format(len(self.socket_clients), len(self.socket_rooms)))

    def _socketWatcherNotifier(self):
        if self.socket_watcher_timer != None:
            self.socket_watcher_timer.cancel()
        self.socket_watcher_timer = threading.Timer(1,self._socketWatcherInfo)
        self.socket_watcher_timer.start()

    def onSocketConnect(self, sid):
        with self.socketio_client_lock:
            logging.info("Websocket: connect '{}'".format(sid))
            self.socket_clients[request.sid] = {}
        self._socketWatcherNotifier()

    def onSocketDisconnect(self, sid):
        with self.socketio_client_lock:
            logging.info("Websocket: disconnect '{}'".format(sid))
            for room in list(self.socket_rooms.keys()):
                if sid not in self.socket_rooms[room]:
                    continue
                self._onSocketRoomLeave(sid, room)
            del self.socket_clients[request.sid]
        self._socketWatcherNotifier()

    def onSocketRoomJoin(self, sid, room, data = None):
        with self.socketio_client_lock:
            logging.info("Websocket: join '{}' - '{}'".format(room, sid))
            if room not in self.socket_rooms:
                logging.info("Websocket: create room '{}'".format(room))
                self.socket_rooms[room] = []
            self.socket_rooms[room].append(sid)
        join_room(room)
        self._socketWatcherNotifier()

    def onSocketRoomLeave(self, sid, room):
        with self.socketio_client_lock:
            self._onSocketRoomLeave(sid, room)
            #if sid in self.socket_rooms[room]:
            #else:
            #    logging.warn("Websocket: Unknown client can't leave '{}' - '{}'".format(room, sid))
        self._socketWatcherNotifier()

    def _onSocketRoomLeave(self, sid, room):
        logging.info("Websocket: leave '{}' - '{}'".format(room, sid))
        try:
            self.socket_rooms[room].remove(sid)
            if len(self.socket_rooms[room]) == 0:
                logging.info("Websocket: close room '{}'".format(room))
                del self.socket_rooms[room]
        except KeyError:
            logging.error("Websocket: room '{}' not registered".format(room))
        leave_room(room)

    def getSocketClients(self, room = None):
        if room is None:
            return self.socket_clients
        return self.socket_rooms[room] if room in self.socket_rooms else []

    def setSocketClientValue(self, sid, field, value):
        self.socket_clients[sid][field] = value

    def getSocketClientValue(self, sid, field):
        return self.socket_clients[sid][field] if field in self.socket_clients[sid] else None

    def isSocketRoomActive(self, room):
        return room in self.socket_rooms

    def areSocketClientsActive(self):
        return len(self.socket_clients) > 0

    def getSocketClient(self):
        return request.sid

    def emitSocketData(self, topic, data, to = None):
        #logging.info("Websocket: emit '{}' to '{}'".format(topic, to))
        #with serverWeb.app_context():
        with self.socketio_emint_lock:
            return serverSocket.emit(topic, data, to = to)

    def getStateMetrics(self):
        return ""

@serverWeb.route('/metrics/', methods = ['GET'])
def metrics():
    return Response(Server.serverHandler.getStateMetrics(), mimetype='text/plain')

@serverSocket.on_error_default
def on_error(e):
    logging.error(e)
    sys.excepthook(*sys.exc_info())

@serverSocket.on('connect')
def on_connect():
    Server.serverHandler.onSocketConnect(request.sid)

@serverSocket.on('disconnect')
def on_disconnect():
    Server.serverHandler.onSocketDisconnect(request.sid)

@serverSocket.on('join')
def on_join(room, data = None):
    Server.serverHandler.onSocketRoomJoin(request.sid, room, data)

@serverSocket.on('leave')
def on_leave(room):
    Server.serverHandler.onSocketRoomLeave(request.sid, room)

Server.initLogger(logging.INFO)

