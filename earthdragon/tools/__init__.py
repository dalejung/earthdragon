from itertools import cycle, islice, chain

from .follow import Follow
from .trace import trace
from .timer import Timer
from .reloader import reimport
try:
    import line_profiler
except ImportError:
    pass
else:
    from .profiler import Profiler

try:
    import ipdb
except ImportError:
    pass
else:
    from .debugtrace import DebugTrace


def roundrobin(*iterables):
    "roundrobin('ABC', 'D', 'EF') --> A D E B F C"
    # Recipe credited to George Sakkis
    pending = len(iterables)
    nexts = cycle(iter(it).__next__ for it in iterables)
    while pending:
        try:
            for next in nexts:
                yield next()
        except StopIteration:
            pending -= 1
            nexts = cycle(islice(nexts, pending))


def chunker(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def flatten(lst):
    result = []
    list(map(result.extend, lst))
    return result


def windowed(iterable, stride=2):
    """
    list(windowed(range(5))) -> [(0, 1), (1, 2), (2, 3), (3, 4)]
    """
    return zip(*[islice(iterable, i, None) for i in range(stride)])
