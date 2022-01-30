#from __future__ import print_function
import sys

logHandler = None

def setLogger(logger):
    global logHandler
    logHandler = logger

def error(*args, **kwargs):
    if logHandler is not None:
        logHandler.error(*args, **kwargs)
    else:
        print(*args, file=sys.stderr, **kwargs)
    
def info(*args, **kwargs):
    if logHandler is not None:
        logHandler.info(*args, **kwargs)
    else:
        print(*args, file=sys.stdout, **kwargs)
