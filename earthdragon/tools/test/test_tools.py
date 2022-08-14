import time
import pytest

from .. import (
    windowed,
    Timer,
)


def test_windowed():
    res = windowed(range(5))
    assert list(res) == [(0, 1), (1, 2), (2, 3), (3, 4)]

    res = windowed(zip(range(5), range(5)))
    # This was breaking. Popped in more_itertools.windowed to fix.
    # The previous version was breaking since zip() will exhaust itself.
    assert list(res) == [
        ((0, 0), (1, 1)),
        ((1, 1), (2, 2)),
        ((2, 2), (3, 3)),
        ((3, 3), (4, 4))
    ]


def test_timer():
    with Timer() as t1:
        time.sleep(0.01)

    with Timer() as t2:
        time.sleep(0.02)

    assert t2 > t1
    assert t1 < t2
    assert t1 != t2
