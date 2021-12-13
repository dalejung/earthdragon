import pytest

from .. import (
    windowed
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
