import ctypes
import ctypes.util
import errno
import os
import logging
from pathlib import Path


NAMESPACE_NAMES = frozenset(['mnt', 'ipc', 'net', 'pid', 'user', 'uts'])

CLONE_NEWNS     = 0x00020000   # New mount namespace group
CLONE_NEWCGROUP = 0x02000000   # New cgroup namespace
CLONE_NEWUTS    = 0x04000000   # New utsname namespace
CLONE_NEWIPC    = 0x08000000   # New ipc namespace
CLONE_NEWUSER   = 0x10000000   # New user namespace
CLONE_NEWPID    = 0x20000000   # New pid namespace
CLONE_NEWTIME	= 0x00000080   # New time namespace
CLONE_NEWNET    = 0x40000000   # New network namespace

# TODO libc function can be replaced with os.setns in python 3.12

def Host():
    #"/usr/bin/nsenter", "-t", "1", "-m", "-u", "-n", "-i"
    #  |
    return Process(1)

def Process(pid):
    return Namespace(pid, CLONE_NEWNS | CLONE_NEWCGROUP | CLONE_NEWUTS | CLONE_NEWIPC | CLONE_NEWNET )

class Namespace(object):
    _libc = ctypes.CDLL(ctypes.util.find_library('c'), use_errno=True)

    def __init__(self, pid, ns_type):
        self.pid = pid
        self.ns_type = ns_type

        self.target_fileno = os.pidfd_open(pid)

        self.parent_fileno = os.pidfd_open(os.getppid())

    #def _close_files(self):
    #    try:
    #        self.target_fd.close()
    #    except:
    #        pass

    #    if self.parent_fd is not None:
    #        self.parent_fd.close()

    def __enter__(self):
        #logging.info('Entering %s namespace %s from %s', self.ns_type, self.pid, os.getpid())

        if self._libc.setns(self.target_fileno, self.ns_type) == -1:
            e = ctypes.get_errno()
            #self._close_files()
            raise OSError(e, errno.errorcode[e])

    def __exit__(self, type, value, tb):
        #logging.info('Leaving %s namespace %s to %s', self.ns_type, self.pid, os.getpid())

        if self._libc.setns(self.parent_fileno, self.ns_type) == -1:
            e = ctypes.get_errno()
            #self._close_files()
            raise OSError(e, errno.errorcode[e])

        #self._close_files()
