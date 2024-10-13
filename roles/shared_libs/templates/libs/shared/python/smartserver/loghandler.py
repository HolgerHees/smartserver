import logging
import logging.handlers
import os
import sys

HANDLER_TYPE_STDOUT = 1
HANDLER_TYPE_JOURNAL = 2

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

class CustomHandler(logging.Handler):
    on_same_line = False
    def emit(self, record):
        try:
            msg = self.format(record)

            level = record.levelname
            if record.levelno == logging.DEBUG:
                journal_level = "debug"
            elif record.levelno == logging.INFO:
                journal_level = "info"
            elif record.levelno == logging.WARNING:
                journal_level = "warning"
            elif record.levelno == logging.ERROR:
                journal_level = "err"
            else:
                journal_level = "crit"

            os.system('echo "{}"  | systemd-cat -t nvidia_exporter -p "{}"'.format("[{}] - {}".format(level, msg), journal_level))
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

def init(handler_type, with_time = True, max_level = logging.INFO):
    if handler_type == HANDLER_TYPE_JOURNAL:
        handler = CustomHandler()
    else:
        handler = logging.StreamHandler(sys.stdout)

    handler.setFormatter(CustomFormatter(
        "%(asctime)s - [%(levelname)s] - [%(custom_module)s] - %(message)s" if with_time else "[%(levelname)s] - [%(custom_module)s] - %(message)s"
    ))

    logging.basicConfig(
        handlers = [handler],
        level=max_level,
        datefmt="%d.%m.%Y %H:%M:%S"
    )
