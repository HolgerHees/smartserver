import json
import os

class ConfigHelper():
    @staticmethod
    def write( config, filename ):
        tmp_filename = filename + "~"
        with open(tmp_filename, 'w') as file:
            json.dump( config, file)
        os.rename(tmp_filename, filename)
