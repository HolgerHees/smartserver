import logging
import time
import threading
import os
from datetime import datetime, timezone, timedelta

from smartserver.confighelper import ConfigHelper
from smartserver import inotify
from smartserver import command
from smartserver.metric import Metric

from lib._process import Process


class INotifyWatcher(threading.Thread):
    def __init__(self, config, inotify_processor, start_lazy_callback):
        threading.Thread.__init__(self)

        self.is_running = False
        self.config = config
        self.inotify_processor = inotify_processor

        self.main_event = threading.Event()

        self.inotify = inotify.INotify(self._inotifyEvent)

        self.init_event = threading.Event()
        self.init_file_scan_process = Process(self.config.cmd_file_scan)
        #self.init_memories_process = Process(self.config.cmd_memorial_index)

        utc_offset_sec = time.altzone if time.localtime().tm_isdst else time.timezone
        utc_offset = timedelta(seconds=-utc_offset_sec)
        self.timezone = timezone(offset=utc_offset)

        self.start_lazy_callback = start_lazy_callback

        self.watched_directories = {}

        self.app_state = -1

        self.dump_path= "/var/lib/nextcloud_service/state.json"

        self.valid_dump_file = True
        self.version = 2

    def start(self):
        self.is_running = True

        self._restore()

        self.inotify.start()

        super().start()

    def terminate(self):
        if not self.is_running:
            return

        if os.path.exists(self.dump_path):
            self._dump()

        self.is_running = False

        self.inotify.stop()
        self.inotify.join()

        self.init_event.set()
        self.init_file_scan_process.terminate()
        self.init_file_scan_process.join()
        #self.init_memories_process.terminate()
        #self.init_memories_process.join()

        self.main_event.set()
        self.join()

    def _restore(self):
        self.valid_dump_file, data = ConfigHelper.loadConfig(self.dump_path, self.version)
        if data is not None:
            self.state = data
        else:
            self.state = {'last_modified': None}
            self._dump()

    def _dump(self):
        if self.valid_dump_file:
            ConfigHelper.saveConfig(self.dump_path, self.version, self.state )

    def _add(self, directory):
        self.watched_directories[directory] = True
        self.inotify.add_watch(directory, inotify.Constants.IN_CLOSE_WRITE | inotify.Constants.IN_CREATE | inotify.Constants.IN_MOVED_FROM | inotify.Constants.IN_MOVED_TO | inotify.Constants.IN_DELETE )
        #logging.info("Watch " + directory)

    def _addRecursive(self, directory):
        self._add(directory)
        if self.is_running:
            for root, sub_directory_names, files in os.walk(directory):
                for _sub_directory_name in sub_directory_names:
                    if not self.is_running:
                        break
                    self._add(os.path.join(root, _sub_directory_name))
                if not self.is_running:
                    break

    def _del(self, directory):
        del self.watched_directories[directory]
        self.inotify.rm_watch(directory)
        #logging.info("Unwatch " + directory)

    def _delRecursive(self, directory):
        self._del(directory)
        if self.is_running:
            for subdirectory in list(self.watched_directories.keys()):
                if subdirectory.startswith(directory):
                    self._del(subdirectory)
                if not self.is_running:
                    break

    def _inotifyEvent(self, event):
        #logging.info(str(event))

        now = datetime.now().replace(microsecond=0, tzinfo=self.timezone)
        is_dir = event.mask & inotify.Constants.IN_ISDIR

        if is_dir and event.path in self.watched_directories:
            directory = event.path
            if event.mask & inotify.Constants.IN_DELETE:
                self._del(directory)
            elif event.mask & inotify.Constants.IN_MOVED_FROM:
                self._delRecursive(directory)
        else:
            # ignore nextcloud memories exif tool modifications
            if not is_dir and event.path.endswith("_exiftool_tmp"):
                return

            directory = event.path if is_dir else os.path.dirname(event.path)
            if directory not in self.watched_directories:
                if event.mask & inotify.Constants.IN_CREATE:
                    self._add(directory)
                elif event.mask & inotify.Constants.IN_MOVED_TO:
                    self._addRecursive(directory)

        self.inotify_processor.trigger(event, now)

    def confirmEvent(self, time):
        self.state['last_modified'] = time.isoformat()

    def _runInitApp(self, process):
        while self.is_running:
            runtime = process.run(lambda msg: logging.info(msg))
            if process.hasErrors():
                logging.info("Not able to run nextcloud '{}' app. Try again in 60 seconds.".format(process.getApp()))
                self.init_event.wait(60)
                self.init_event.clear()
            elif not self.is_running or process.isShutdown():
                interrupted = True
                break
            else:
                logging.info("Finished nextcloud '{}' app in {:.1f} seconds".format(process.getApp(), runtime))
                break

    def run(self):
        logging.info("INotify watcher started")
        try:
            start = time.time()
            detected_last_modified = None
            interrupted = False
            for directory in self.config.watched_directories:
                self._addRecursive(directory)
                if not self.is_running:
                    break
                result = command.exec("find {} -type f -printf \"%T+\t%p\n\" | sort | tail -1".format(directory), exitstatus_check=False, namespace_pid=command.NAMESPACE_PID_HOST)
                if result.returncode != 0:
                    if not self.is_running or result.returncode == Process.SIGNAL_TERM:
                        interrupted = True
                        break
                    raise Exception(result.stdout.decode("utf-8"))
                date_str, _ = result.stdout.decode("utf-8").split("\t")

                date =  datetime.fromisoformat(date_str).replace(microsecond=0, tzinfo=self.timezone)

                if detected_last_modified is None or detected_last_modified < date:
                    detected_last_modified = date

            if self.is_running and not interrupted:
                end = time.time()
                logging.info("INotify watcher initialized {} directories in {:.1f} seconds".format(len(self.watched_directories.keys()), end-start))

                last_modified = datetime.fromisoformat(self.state['last_modified']) if self.state['last_modified'] is not None else None
                if last_modified is None or detected_last_modified > last_modified:
                    self._runInitApp(self.init_file_scan_process)

                    #if self.is_running and not interrupted:
                    #    self._runInitApp(self.init_memories_process)

                    if self.is_running and not interrupted:
                        self.state['last_modified'] = detected_last_modified.isoformat()
                        self._dump()
                else:
                    logging.info("Skipped file scanning")

                if self.is_running and not interrupted:
                    self.start_lazy_callback()

            while self.is_running:
                self.main_event.wait(60)
                self.main_event.clear()

        except Exception as e:
            self.is_running = False
            raise e
        finally:
            logging.info("INotify watcher stopped")

    def getStateMetrics(self):
        return [
            Metric.buildProcessMetric("nextcloud_service", "inotify_watcher", "1" if self.is_running else "0"),
            Metric.buildStateMetric("nextcloud_service", "inotify_watcher", "cache_file", "1" if self.valid_dump_file else "0"),
            Metric.buildStateMetric("nextcloud_service", "inotify_watcher", "app", "1" if not self.init_file_scan_process.hasErrors() else "0", { "app": self.init_file_scan_process.getApp() }),
            #Metric.buildStateMetric("nextcloud_service", "inotify_watcher", "app", "1" if not self.init_memories_process.hasErrors() else "0", { "app": self.init_memories_process.getApp() }),
            Metric.buildDataMetric("nextcloud_service", "inotify_watcher", "count", len(self.watched_directories))
        ]
