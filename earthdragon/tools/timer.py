import time
import sys

class Timer:
    """
        Usage:

        with Timer() as t:
            ret = func(df)
        print(t.interval)
    """
    runs = []

    def __init__(self, name='', verbose=True):
        self.name = name
        self.verbose = verbose
        self.start = None
        self.wall_start = None
        self.end = None
        self.wall_end = None
        Timer.runs.append(self)

    def clear_runs(self):
        Timer.runs = []

    def __enter__(self):
        self.start = time.clock()
        self.wall_start = time.time()
        return self

    def __exit__(self, *args):
        self.end = time.clock()
        self.wall_end = time.time()
        self.interval = self.end - self.start
        self.wall_interval = self.wall_end - self.wall_start

        if self.verbose:
            print((self.msg))

    @property
    def msg(self):
        msg = "Run {name}: CPU time: {interval}  Wall time: {wall_interval}"
        return msg.format(name=self.name, interval=_format_time(self.interval),
                         wall_interval=_format_time(self.wall_interval))

    def __str__(self):
        return self.msg

    def __repr__(self):
        if self.start is None:
            return "Timer(name={name})".format(**self.__dict__)
        msg = "Timer(name={name}, interval={interval},wall_interval={wall_interval})"
        return msg.format(**self.__dict__)

# grabbed from IPython/core/magics/execution.py
def _format_time(timespan, precision=3):
    """Formats the timespan in a human readable form"""
    import math

    if timespan >= 60.0:
        # we have more than a minute, format that in a human readable form
        # Idea from http://snipplr.com/view/5713/
        parts = [("d", 60*60*24),("h", 60*60),("min", 60), ("s", 1)]
        time = []
        leftover = timespan
        for suffix, length in parts:
            value = int(leftover / length)
            if value > 0:
                leftover = leftover % length
                time.append('%s%s' % (str(value), suffix))
            if leftover < 1:
                break
        return " ".join(time)


    # Unfortunately the unicode 'micro' symbol can cause problems in
    # certain terminals.
    # See bug: https://bugs.launchpad.net/ipython/+bug/348466
    # Try to prevent crashes by being more secure than it needs to
    units = ["s", "ms",'us',"ns"] # the save value
    if hasattr(sys.stdout, 'encoding') and sys.stdout.encoding:
        try:
            '\xb5'.encode(sys.stdout.encoding)
            units = ["s", "ms",'\xb5s',"ns"]
        except:
            pass
    scaling = [1, 1e3, 1e6, 1e9]

    if timespan > 0.0:
        order = min(-int(math.floor(math.log10(timespan)) // 3), 3)
    else:
        order = 3
    ret =  "%.*g %s" % (precision, timespan * scaling[order], units[order])
    return ret

