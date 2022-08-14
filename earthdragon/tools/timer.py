import time
import sys
import math
from functools import total_ordering


class TimerSet:
    def __init__(self, timers):
        self.timers = timers

    @property
    def max_timer(self):
        return max(self.timers)

    @property
    def max(self):
        return self.max_timer.wall_interval

    @property
    def min_timer(self):
        return min(self.timers)

    @property
    def min(self):
        return self.min_timer.wall_interval

    def __repr__(self):
        n = len(self.timers)
        min = self.min
        max = self.max
        return f"TimerSet({n=}, {min=}, {max=})"


@total_ordering
class Timer:
    """
        Usage:

        with Timer() as t:
            ret = func(df)
        print(t.interval)
    """
    runs = []

    def __init__(self, name='noname', verbose=True):
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
        self.start = time.process_time()
        self.wall_start = time.perf_counter()
        return self

    def __exit__(self, *args):
        self.end = time.process_time()
        self.wall_end = time.perf_counter()
        self.interval = self.end - self.start
        self.wall_interval = self.wall_end - self.wall_start

        if self.verbose:
            print((self.msg))

    @property
    def msg(self):
        msg = "Run {name}: CPU time: {interval}  Wall time: {wall_interval}"
        return msg.format(name=self.name, interval=format_time(self.interval),
                          wall_interval=format_time(self.wall_interval))

    def __str__(self):
        return self.msg

    def __repr__(self):
        name = self.name

        if self.start is None:
            return f"Timer({name=})"

        interval = self.interval
        wall_interval = self.wall_interval
        return f"Timer({name=}, {interval=}, {wall_interval=})"

    @property
    def wall_interval_string(self):
        return format_time(self.wall_interval)

    def __eq__(self, other):
        return self.wall_interval == other.wall_interval

    def __gt__(self, other):
        return self.wall_interval > other.wall_interval

    @classmethod
    def repeat(cls, func, n=3):
        timers = []
        for x in range(n):
            with cls(verbose=False) as t:
                func()

            timers.append(t)

        return TimerSet(timers)



# grabbed from IPython/core/magics/execution.py
def format_time(timestamp, precision=3, tmpl=None):
    if tmpl is None:
        tmpl = f"{{0:.{precision}g}}{{1}}"
    return " ".join(map(lambda x: tmpl.format(*x), _format_time(timestamp)))


def _format_time(timespan):
    """
    Formats the timespan in a human readable form

    Expects timespan in seconds.
    """

    if timespan >= 60.0:
        # we have more than a minute, format that in a human readable form
        # Idea from http://snipplr.com/view/5713/
        parts = [('d', 60*60*24), ('h', 60*60), ('min', 60), ('s', 1)]
        time = []
        leftover = timespan
        for suffix, length in parts:
            value = int(leftover / length)
            if value > 0:
                leftover = leftover % length
                time.append(u'%s%s' % (str(value), suffix))
                yield value, suffix
                if leftover < 1:
                    break
        return

    # Unfortunately the unicode 'micro' symbol can cause problems in
    # certain terminals.
    # See bug: https://bugs.launchpad.net/ipython/+bug/348466
    # Try to prevent crashes by being more secure than it needs to
    # E.g. eclipse is able to print a µ, but has no sys.stdout.encoding set.
    units = ['s', 'ms', 'us', 'ns']  # the save value
    if hasattr(sys.stdout, 'encoding') and sys.stdout.encoding:
        try:
            '\xb5'.encode(sys.stdout.encoding)
            units = ['s', 'ms', '\xb5s', 'ns']
        except Exception:
            pass
    scaling = [1, 1e3, 1e6, 1e9]

    if timespan > 0.0:
        order = min(-int(math.floor(math.log10(timespan)) // 3), 3)
    else:
        order = 3
    value = timespan * scaling[order]
    suffix = units[order]
    yield value, suffix
