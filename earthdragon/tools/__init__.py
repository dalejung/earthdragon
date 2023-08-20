from itertools import (
    cycle,
    islice,
    chain,
)
import more_itertools

from .follow import Follow as Follow
from .trace import trace as trace
from .timer import Timer as Timer
from .reloader import reimport as reimport

try:
    import line_profiler   # noqa: F401
except ImportError:
    pass
else:
    from .profiler import Profiler

try:
    import ipdb   # noqa: F401
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
    return more_itertools.windowed(iterable, n=stride)


def merge_dicts(*dict_args):
    return dict(chain.from_iterable(d.items() for d in dict_args))


__all__ = [
    'merge_dicts',
    'roundrobin',
    'chunker',
    'flatten',
    'windowed',
    'Profiler',
    'reimport',
    'Follow',
    'trace',
    'Timer',
    'DebugTrace',
]
