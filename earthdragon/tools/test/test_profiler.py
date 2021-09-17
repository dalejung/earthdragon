from ..profiler import Profiler
import io

def but(e=None):
    import time
    time.sleep(.1)

stream = io.StringIO()

with Profiler(but, stream=stream) as p:
    but()

stream.seek(0)
output = stream.read()
assert "time.sleep(.1)" in output
