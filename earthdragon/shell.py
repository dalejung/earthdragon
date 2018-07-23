import subprocess
import os
from contextlib import contextmanager

def run(cmd, **kwargs):
    if kwargs:
        cmd = cmd.format(**kwargs)
    out = subprocess.check_output(cmd, shell=True)
    return out.decode('utf-8')

@contextmanager
def pushd(new_dir):
    previous_dir = os.getcwd()
    os.chdir(new_dir)
    try:
        yield
    finally:
        os.chdir(previous_dir)
