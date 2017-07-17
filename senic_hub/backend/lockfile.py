from fasteners import InterProcessLock


def open_locked(file, mode, buffering=-1, encoding=None, errors=None, newline=None, closefd=True):
    """
    Returns an instance of `FileLock` that can be used in a with statement.

    If used in a with statement, an inter-process lock for `file` will be acquired and the file
    will be opened. If the file is already locked by another `open_locked` call then the call
    blocks until the lock has been released. When the with statement has completed, the lock
    will be released. The lock is stored in a file with the same filename that additionally
    carries a .lock extension.

    All file related parameters are the same as in Python's `open()` method as they are simply
    forwarded to `open()`.
    """
    return _LockFile(file, mode, buffering, encoding, errors, newline, closefd)


class _LockFile:
    def __init__(self, file, mode, buffering, encoding, errors, newline, closefd):
        self.file = file
        self.mode = mode
        self.buffering = buffering
        self.encoding = encoding
        self.errors = errors
        self.newline = newline
        self.closefd = closefd
        self.f = None
        self.lock = InterProcessLock(file + '.lock')

    def __enter__(self):
        with self.lock:
            self.f = open(self.file, self.mode, self.buffering, self.encoding, self.errors, self.newline, self.closefd)
            return self.f

    def __exit__(self, type, value, traceback):
        self.f.close()
