"""Provides `subprocess.run()` from Python 3.5+ if available. Otherwise falls back to `subprocess.check_output()`."""

try:
    from subprocess import run
except ImportError:
    from collections import namedtuple
    from subprocess import check_output, CalledProcessError

    def run(args, *, stdin=None, input=None, stdout=None, stderr=None, shell=False, timeout=None, check=False,
            encoding=None, errors=None):
        try:
            stdout_bytes = check_output(args, stdin=stdin, stderr=stderr, shell=shell, timeout=timeout)
        except CalledProcessError as e:
            if check:
                raise
            else:
                stdout_bytes = e.output
        Output = namedtuple('Output', ['stdout'])
        return Output(stdout=stdout_bytes)
