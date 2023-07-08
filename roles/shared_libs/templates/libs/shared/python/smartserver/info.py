import requests

import traceback
import logging

class Info():
    @staticmethod
    def isDefaultISPConnectionActive():
        try:
            response = requests.get("http://127.0.0.1:8507/default_isp_state/")
            return True if response.content == b"active" else False
        except requests.exceptions.ConnectionError:
            return False
        except:
            logging.error(traceback.format_exc())
            return False
