import struct
import threading
from ctypes import CFUNCTYPE, CDLL, get_errno, c_int, c_char_p, c_uint32
from termios import FIONREAD
from fcntl import ioctl
from time import sleep
from functools import reduce
import os

# https://github.com/gorakhargosh/watchdog/blob/master/src/watchdog/observers/inotify_c.py
# https://github.com/seb-m/pyinotify/blob/master/python3/pyinotify.py
# https://github.com/chrisjbillington/inotify_simple/blob/master/inotify_simple.py

libc = CDLL(None)

if not hasattr(libc, "inotify_init") or not hasattr(libc, "inotify_add_watch") or not hasattr(libc, "inotify_rm_watch"):
    raise Exception(f"Unsupported libc version found: {libc._name}")

inotify_add_watch = CFUNCTYPE(c_int, c_int, c_char_p, c_uint32, use_errno=True)(("inotify_add_watch", libc))

inotify_rm_watch = CFUNCTYPE(c_int, c_int, c_uint32, use_errno=True)(("inotify_rm_watch", libc))

inotify_init = CFUNCTYPE(c_int, use_errno=True)(("inotify_init", libc))

class Constants:
    # User-space events
    IN_ACCESS = 0x00000001  # File was accessed.
    IN_MODIFY = 0x00000002  # File was modified.
    IN_ATTRIB = 0x00000004  # Meta-data changed.
    IN_CLOSE_WRITE = 0x00000008  # Writable file was closed.
    IN_CLOSE_NOWRITE = 0x00000010  # Unwritable file closed.
    IN_OPEN = 0x00000020  # File was opened.
    IN_MOVED_FROM = 0x00000040  # File was moved from X.
    IN_MOVED_TO = 0x00000080  # File was moved to Y.
    IN_CREATE = 0x00000100  # Subfile was created.
    IN_DELETE = 0x00000200  # Subfile was deleted.
    IN_DELETE_SELF = 0x00000400  # Self was deleted.
    IN_MOVE_SELF = 0x00000800  # Self was moved.

    # Events sent by the kernel to a watch.
    IN_UNMOUNT = 0x00002000  # Backing file system was unmounted.
    IN_Q_OVERFLOW = 0x00004000  # Event queued overflowed.
    IN_IGNORED = 0x00008000  # File was ignored.

    # Special flags.
    IN_ONLYDIR = 0x01000000  # Only watch the path if it's a directory.
    IN_DONT_FOLLOW = 0x02000000  # Do not follow a symbolic link.
    IN_EXCL_UNLINK = 0x04000000  # Exclude events on unlinked objects
    IN_MASK_ADD = 0x20000000  # Add to the mask of an existing watch.
    IN_ISDIR = 0x40000000  # Event occurred against directory.
    IN_ONESHOT = 0x80000000  # Only send event once.

    # Flags for ``inotify_init1``
    IN_CLOEXEC = 0x02000000
    IN_NONBLOCK = 0x00004000

    # Helper user-space events.
    IN_CLOSE = IN_CLOSE_WRITE | IN_CLOSE_NOWRITE  # Close.
    IN_MOVE = IN_MOVED_FROM | IN_MOVED_TO  # Moves.

    # All user-space events.
    IN_ALL_EVENTS = reduce(
        lambda x, y: x | y,
        [
            IN_ACCESS,
            IN_MODIFY,
            IN_ATTRIB,
            IN_CLOSE_WRITE,
            IN_CLOSE_NOWRITE,
            IN_OPEN,
            IN_MOVED_FROM,
            IN_MOVED_TO,
            IN_DELETE,
            IN_CREATE,
            IN_DELETE_SELF,
            IN_MOVE_SELF,
        ],
    )

# we cares only about these events.
ALL_EVENTS = reduce(
    lambda x, y: x | y,
    [
        Constants.IN_MODIFY,
        Constants.IN_ATTRIB,
        Constants.IN_MOVED_FROM,
        Constants.IN_MOVED_TO,
        Constants.IN_CREATE,
        Constants.IN_DELETE,
        Constants.IN_DELETE_SELF,
        Constants.IN_DONT_FOLLOW,
        Constants.IN_CLOSE_WRITE,
        Constants.IN_OPEN
    ],
)


'''class inotify_event_struct(ctypes.Structure):
    """
    Structure representation of the inotify_event structure
    (used in buffer size calculations)::

        struct inotify_event {
            __s32 wd;            /* watch descriptor */
            __u32 mask;          /* watch mask */
            __u32 cookie;        /* cookie to synchronize two events */
            __u32 len;           /* length (including nulls) of name */
            char  name[0];       /* stub for possible name */
        };
    """

    _fields_ = [
        ("wd", c_int),
        ("mask", c_uint32),
        ("cookie", c_uint32),
        ("len", c_uint32),
        ("name", c_char_p),
    ]'''

EVENT_META_FMT = 'iIII'
EVENT_META_SIZE = struct.calcsize(EVENT_META_FMT)

class INotify(threading.Thread):
    def __init__(self, callback):
        super(INotify, self).__init__()

        self.is_running = False

        self._inotify_fd = inotify_init()

        self.callback = callback

        self._wd_for_path = {}
        self._path_for_wd = {}

    def add_watch(self, path, mask = None):
        if mask is None:
            mask = ALL_EVENTS

        wd = inotify_add_watch(self._inotify_fd, os.fsencode(path), mask)
        if wd == -1:
            INotify._raise_error()

        self._wd_for_path[path] = wd
        self._path_for_wd[wd] = path

        return wd

    def rm_watch(self, path):
        wd = self._wd_for_path[path]
        if inotify_rm_watch(self._inotify_fd, wd) == -1:
            INotify._raise_error()

        del self._wd_for_path[path]
        del self._path_for_wd[wd]

    def run(self):
        while self.is_running:
            bytes_avail = c_int()
            ioctl(self._inotify_fd, FIONREAD, bytes_avail)
            if not bytes_avail.value:
                sleep(0.1)
                continue
            event_buffer = os.read(self._inotify_fd, bytes_avail.value)

            for wd, mask, cookie, name in INotify._parse_event_buffer(event_buffer):
                if wd == -1:
                    continue

                self.callback(INotifyEvent(wd, mask, cookie, name, self._path_for_wd[wd]))

        try:
            os.close(self._inotify_fd)
        except OSError:
            pass

    def start(self):
        self.is_running = True
        super().start()

    def stop(self):
        self.is_running = False

    @staticmethod
    def _raise_error():
        err = get_errno()
        if err == errno.ENOSPC:
            raise OSError(errno.ENOSPC, "inotify watch limit reached")
        elif err == errno.EMFILE:
            raise OSError(errno.EMFILE, "inotify instance limit reached")
        elif err != errno.EACCES:
            raise OSError(err, os.strerror(err))

    @staticmethod
    def _parse_event_buffer(event_buffer):
        i = 0
        while i + EVENT_META_SIZE <= len(event_buffer):
            wd, mask, cookie, length = struct.unpack_from(EVENT_META_FMT, event_buffer, i)
            name = event_buffer[i + EVENT_META_SIZE : i + EVENT_META_SIZE + length].rstrip(b"\0")
            i += EVENT_META_SIZE + length
            yield wd, mask, cookie, name

class INotifyEvent:
    """
    Inotify event struct wrapper.

    :param wd:
        Watch descriptor
    :param mask:
        Event mask
    :param cookie:
        Event cookie
    :param name:
        Base name of the event source path.
    :param wd_path:
        Full event source path.
    """

    def __init__(self, wd, mask, cookie, name, wd_path):
        self._wd = wd
        self._mask = mask
        self._cookie = cookie
        self._name = name
        self._wd_path = wd_path

        self._path = wd_path + ( "/" + os.fsdecode(name) if name else "" )

    @property
    def wd(self):
        return self._wd

    @property
    def mask(self):
        return self._mask

    @property
    def cookie(self):
        return self._cookie

    @property
    def name(self):
        return self._name

    @property
    def wd_path(self):
        return self._wd_path

    @property
    def path(self):
        return self._path

    @staticmethod
    def _get_mask_string(mask):
        masks = []
        for c in dir(Constants):
            if not c.startswith("IN_") or c in [
                "IN_ALL_EVENTS",
                "IN_CLOSE",
                "IN_MOVE",
            ]:
                continue

            c_val = getattr(Constants, c)
            if mask & c_val:
                masks.append(c)
        return "|".join(masks)

    def __repr__(self):
        return (
            f"<event path={self.path!r}, mask={self._get_mask_string(self.mask)}, cookie={self.cookie}, wd={self.wd}>"
        )
