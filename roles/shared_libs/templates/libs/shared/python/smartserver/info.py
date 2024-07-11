import requests

import traceback
import logging

class Info():
    @staticmethod
    def _getConnectionState(server_name):
        try:
            response = requests.get("https://{}/system_service/api/wan_state/".format(server_name))
            return response.content.decode("utf-8")
        except requests.exceptions.ConnectionError:
            return "unknown"
        except:
            logging.error(traceback.format_exc())
            return "unknown"

    @staticmethod
    def isDefaultConnectionActive(server_name):
        return Info._getConnectionState(server_name) == "default"

    @staticmethod
    def isFallbackConnectionActive(server_name):
        return Info._getConnectionState(server_name) == "fallback"

    @staticmethod
    def isConnectionOnline(server_name):
        return Info._getConnectionState(server_name) != "unknown"
