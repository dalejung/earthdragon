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

    with Timer() as t3:
        time.sleep(0.03)

    timers = [t1, t2, t3]

    max_t = max(timers)
    assert max_t is t3

    min_t = min(timers)
    assert min_t is t1


def test_timer_set():
    x = 1

    def sleep_more():
        nonlocal x
        time.sleep(0.001 * x)
        x += 1

    timerset = Timer.repeat(sleep_more, n=10)
    assert timerset.max_timer is timerset.timers[-1]
    assert timerset.min_timer is timerset.timers[0]
    assert timerset.min < 0.002
    assert timerset.max > 0.01
