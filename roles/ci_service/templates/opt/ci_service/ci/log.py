#from __future__ import print_function
import sys

def error(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)
    
def info(*args, **kwargs):
    print(*args, file=sys.stdout, **kwargs)
