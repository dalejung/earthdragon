import os
from tempfile import TemporaryDirectory


def touch(fname, times=None):
    with open(fname, 'a'):
        os.utime(fname, times)


class fake_file_system(TemporaryDirectory):
    pass
