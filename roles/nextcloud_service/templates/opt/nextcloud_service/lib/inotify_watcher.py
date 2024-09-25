import logging
import time
import threading
import os
from datetime import datetime, timezone, timedelta

from smartserver.confighelper import ConfigHelper
from smartserver import inotify
from smartserver.command import exec, exec2


class INotifyWatcher(threading.Thread):
    def __init__(self, config, inotify_processor, start_lazy_callback):
        threading.Thread.__init__(self)

        self.is_running = False
        self.config = config
        self.inotify_processor = inotify_processor

        utc_offset_sec = time.altzone if time.localtime().tm_isdst else time.timezone
        utc_offset = timedelta(seconds=-utc_offset_sec)
        self.timezone = timezone(offset=utc_offset)

        self.start_lazy_callback = start_lazy_callback

        self.inotify = inotify.INotify(self._inotifyEvent)

        self.watched_directories = {}

        self.app_state = -1

        self.dump_path= "/var/lib/nextcloud_service/state.json"

        self.valid_dump_file = True
        self.version = 1

    def start(self):
        self.is_running = True

        self._restore()

        self.inotify.start()

        super().start()

    def terminate(self):
        if self.is_running:
            if os.path.exists(self.dump_path):
                self._dump()

            self.is_running = False

            self.inotify.stop()
            self.inotify.join()

    def isRunning(self):
        return self.is_running

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
        for root, sub_directory_names, files in os.walk(directory):
            for _sub_directory_name in sub_directory_names:
                self._add(os.path.join(root, _sub_directory_name))

    def _del(self, directory):
        del self.watched_directories[directory]
        self.inotify.rm_watch(directory)
        #logging.info("Unwatch " + directory)

    def _delRecursive(self, directory):
        self._del(directory)
        for subdirectory in list(self.watched_directories.keys()):
            if subdirectory.startswith(directory):
                self._del(subdirectory)

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
            directory = event.path if is_dir else os.path.dirname(event.path)
            if directory not in self.watched_directories:
                if event.mask & inotify.Constants.IN_CREATE:
                    self._add(directory)
                elif event.mask & inotify.Constants.IN_MOVED_TO:
                    self._addRecursive(directory)

        self.inotify_processor.trigger(event, now)

    def confirmEvent(self, time):
        self.state['last_modified'] = time.isoformat()

    def run(self):
        logging.info("INotify watcher started")
        try:
            start = time.time()
            detected_last_modified = None
            for directory in self.config.watched_directories:
                self._addRecursive(directory)
                result = exec("find {} -type f -printf \"%T+\t%p\n\" | sort | tail -1".format(directory), run_on_host=True)
                date_str, file = result.stdout.decode("utf-8").split("\t")

                date =  datetime.fromisoformat(date_str).replace(microsecond=0, tzinfo=self.timezone)

                if detected_last_modified is None or detected_last_modified < date:
                    detected_last_modified = date
            end = time.time()
            logging.info("INotify watcher initialized {} directories in {:.2f} seconds".format(len(self.watched_directories.keys()), end-start))

            last_modified = datetime.fromisoformat(self.state['last_modified']) if self.state['last_modified'] is not None else None

            #logging.info(detected_last_modified)
            #logging.info(last_modified)
            #logging.info(detected_last_modified > last_modified)

            #last_modified = detected_last_modified

            if last_modified is None or detected_last_modified > last_modified:
                logging.info("Starting file scan")
                while self.is_running:
                    start = time.time()
                    code, result = exec2(self.config.cmd_file_scan, is_running_callback=self.isRunning, run_on_host=True)
                    if code == 0:
                        self.app_state = 1
                        end = time.time()
                        logging.info("Files scanned in {:.2f} seconds".format(end-start))
                        break
                    else:
                        self.app_state = 0
                        logging.info("Not able to run nextcloud 'file scanner' app. Try again in 60 seconds.")
                        self.queue_event.wait(60)
                        self.queue_event.clear()
                        if self.is_running:
                            logging.info("Restart file scan")
                self.state['last_modified'] = detected_last_modified.isoformat()

                self._dump()
            else:
                self.app_state = 1
                logging.info("Skipped file scan")

            self.start_lazy_callback()
        except Exception as e:
            logging.info("INotify processor crashed")
            self.is_running = False
            raise e

    def getStateMetrics(self):
        metrics = [
            "nextcloud_service_process{{type=\"inotify_watcher\",group=\"main\"}} {}".format("1" if self.is_running else "0"),
            "nextcloud_service_process{{type=\"inotify_watcher\",group=\"app\",details=\"files:scan\"}} {}".format(self.app_state),
            "nextcloud_service_state{{type=\"inotify_watcher\",group=\"count\"}} {}".format(len(self.watched_directories))
        ]
        return metrics
