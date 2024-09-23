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

        self.dump_path= "/var/lib/nextcloud_service/state.json"

        self.valid_dump_file = True
        self.version = 1

    def start(self):
        self.is_running = True

        self._restore()

        self.inotify.start()

        super().start()

    def terminate(self):
        if self.is_running and os.path.exists(self.dump_path):
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

        for root, sub_directory_names, files in os.walk(directory):
            for _sub_directory_name in sub_directory_names:
                sub_directory = os.path.join(root, _sub_directory_name)
                self.watched_directories[sub_directory] = True
                self.inotify.add_watch(sub_directory, inotify.Constants.IN_CLOSE_WRITE | inotify.Constants.IN_CREATE | inotify.Constants.IN_MOVED_FROM | inotify.Constants.IN_MOVED_TO | inotify.Constants.IN_DELETE )

    def _del(self, directory):
        del self.watched_directories[directory]
        self.inotify.rm_watch(directory)

        for root, sub_directory_names, files in os.walk(directory):
            for _sub_directory_name in sub_directory_names:
                sub_directory = os.path.join(root, _sub_directory_name)
                del self.watched_directories[sub_directory]
                self.inotify.rm_watch(sub_directory)

    def _inotifyEvent(self, event):
        now = datetime.now().replace(microsecond=0, tzinfo=self.timezone)

        if event.path in self.watched_directories:
            directory = event.path
            if event.mask & ( inotify.Constants.IN_DELETE | inotify.Constants.IN_MOVED_FROM ):
                logging.info("Unwatch " + directory)
                self._del(directory)
        else:
            directory = event.path if event.mask & inotify.Constants.IN_ISDIR else os.path.dirname(event.path)
            if directory not in self.watched_directories and event.mask & ( inotify.Constants.IN_CREATE | inotify.Constants.IN_MOVED_TO ):
                logging.info("Watch " + directory)
                self._add(directory)

        self.inotify_processor.trigger(event, now)

    def confirmEvent(self, time):
        self.state['last_modified'] = time.isoformat()

    def run(self):
        logging.info("INotify watcher started")
        try:
            start = time.time()
            detected_last_modified = None
            for directory in self.config.watched_directories:
                self._add(directory)
                result = exec("find {} -type f -printf \"%T+\t%p\n\" | sort | tail -1".format(directory), shell=True, run_on_host=True)
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
                        end = time.time()
                        logging.info("Files scanned in {:.2f} seconds".format(end-start))
                        break
                    else:
                        logging.info("Not able to scan files. Try again in 60 seconds.")
                        self.queue_event.wait(60)
                        self.queue_event.clear()
                        if self.is_running:
                            logging.info("Restart file scan")
                self.state['last_modified'] = detected_last_modified.isoformat()

                self._dump()
            else:
                logging.info("Skipped file scan")

            self.start_lazy_callback()
        except Exception as e:
            logging.info("INotify processor crashed")
            self.is_running = False
            raise e

    def getStateMetrics(self):
        metrics = [
            "nextcloud_service_process{{job=\"inotify_watcher\"}} {}".format("1" if self.is_running else "0")
        ]
        return metrics
