import os
import logging
import json


class Helper():
    def loadConfig(path, version):
        try:
            if os.path.exists(path):
                with open(path) as f:
                    data = json.load(f)
                    if "version" in data and data["version"] == version:
                        logging.info("Config '{}' loaded".format(path))
                        return True, data
                    else:
                        logging.info("Config '{}' not loaded (wrong version)".format(path))
            else:
                logging.info("Config '{}' is empty".format(path))
            return True, None
        except Exception:
            logging.info("Config '{}' is invalid".format(path))
            return False, None

    def saveConfig(path, version, data):
        with open(path, 'w') as f:
            data["version"] = version
            json.dump( data, f, ensure_ascii=False)
        logging.info("Config '{}' saved".format(path))
