import requests

import traceback
import logging

class Info():
    @staticmethod
    def _getConnectionState():
        try:
            response = requests.get("http://127.0.0.1:8507/wan_state/")
            return response.content.decode("utf-8")
        except requests.exceptions.ConnectionError:
            return "unknown"
        except:
            logging.error(traceback.format_exc())
            return "unknown"

    @staticmethod
    def isDefaultConnectionActive():
        return Info._getConnectionState() == "default"

    @staticmethod
    def isFallbackConnectionActive():
        return Info._getConnectionState() == "fallback"

    @staticmethod
    def isConnectionOnline():
        return Info._getConnectionState() != "unknown"
