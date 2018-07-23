import subprocess

def run(cmd, **kwargs):
    if kwargs:
        cmd = cmd.format(**kwargs)
    out = subprocess.check_output(cmd, shell=True)
    return out.decode('utf-8')

