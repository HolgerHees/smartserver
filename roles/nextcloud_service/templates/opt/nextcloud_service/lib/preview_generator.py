import logging
import threading
import time

from smartserver.command import exec2


class PreviewGenerator(threading.Thread):
    def __init__(self, config):
        threading.Thread.__init__(self)

        self.event = threading.Event()

        self.is_running = False
        self.config = config

        self.app_state = -1
        self.first_event = 0
        self.last_event = 0

    def start(self):
        self.is_running = True
        super().start()

    def terminate(self):
        if self.is_running:
            self.is_running = False
            self.event.set()
            self.join()

    def trigger(self):
        self.last_event = time.time()
        if self.first_event == 0:
            self.first_event = self.last_event
        self.event.set()

    def run(self):
        logging.info("Preview generator started")
        try:
            while self.is_running:
                now = time.time()
                next_timeout = self.config.min_preview_delay - (now - self.last_event)
                max_timeout = self.config.max_preview_delay - (now - self.first_event)
                timeout = next_timeout if next_timeout < max_timeout else max_timeout
                if timeout <= 0:
                    start = time.time()

                    code, result = exec2(self.config.cmd_preview_generator, is_running_callback=self.isRunning, run_on_host=True )
                    if code == 0:
                        self.app_state = 1
                        end = time.time()
                        logging.info("Previews generated in {:.2f} seconds".format(end-start))
                        self.first_event = self.last_event = 0
                        self.event.wait()
                    else:
                        self.app_state = 0
                        logging.info(result)
                        logging.info("Not able to run nextcloud 'preview generator' app. Try again in 60 seconds.")
                        self.event.wait(60)
                        if self.is_running:
                            logging.info("Restart preview generator")
                else:
                    self.event.wait(timeout)
                self.event.clear()
        except Exception as e:
            self.is_running = False
            raise e
        finally:
            logging.info("Preview generator stopped")

    def isRunning(self):
        return self.is_running

    def getStateMetrics(self):
        metrics = [
            "nextcloud_service_process{{type=\"preview_generator\",group=\"main\"}} {}".format("1" if self.is_running else "0"),
            "nextcloud_service_process{{type=\"preview_generator\",group=\"app\",details=\"preview:pre-generate\"}} {}".format(self.app_state)
        ]
        return metrics
