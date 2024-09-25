import logging
import threading
import time
import os

from smartserver import command

from lib._process import Process


class PreviewGenerator(threading.Thread):
    def __init__(self, config):
        threading.Thread.__init__(self)

        self.generator_process = Process()
        self.generator_event = threading.Event()

        self.is_running = False
        self.config = config

        self.first_event = 0
        self.last_event = 0

    def start(self):
        self.is_running = True
        super().start()

    def terminate(self):
        if not self.is_running:
            return

        self.is_running = False

        self.generator_event.set()
        self.generator_process.terminate()
        self.generator_process.join()

        self.join()

    def trigger(self):
        self.last_event = time.time()
        if self.first_event == 0:
            self.first_event = self.last_event
        self.generator_event.set()

    def run(self):
        logging.info("Preview generator started")
        try:
            while self.is_running:
                now = time.time()
                next_timeout = self.config.min_preview_delay - (now - self.last_event)
                max_timeout = self.config.max_preview_delay - (now - self.first_event)
                timeout = next_timeout if next_timeout < max_timeout else max_timeout
                if timeout <= 0:
                    runtime = self.generator_process.run(self.config.cmd_preview_generator, lambda msg: logging.info(msg))
                    if self.generator_process.hasErrors():
                        logging.info("Not able to run nextcloud 'preview generator' app. Try again in 60 seconds.")
                        self.generator_event.wait(60)
                        if self.is_running:
                            logging.info("Restart preview generator")
                    else:
                        if not self.is_running or self.generator_process.isShutdown():
                            break
                        logging.info("Previews generated in {:.2f} seconds".format(runtime))
                        self.first_event = self.last_event = 0
                        self.generator_event.wait()
                else:
                    self.generator_event.wait(timeout)
                self.generator_event.clear()
        except Exception as e:
            self.is_running = False
            raise e
        finally:
            logging.info("Preview generator stopped")

    def getStateMetrics(self):
        metrics = [
            "nextcloud_service_process{{type=\"preview_generator\",group=\"main\"}} {}".format("1" if self.is_running else "0"),
            "nextcloud_service_process{{type=\"preview_generator\",group=\"app\",details=\"preview:pre-generate\"}} {}".format("1" if not self.generator_process.hasErrors() else "0")
        ]
        return metrics
