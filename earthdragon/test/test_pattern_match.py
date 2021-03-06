import pytest
from collections import Counter

from asttools import (
    quick_parse,
)

from ..pattern_match import (
    pattern,
    UnhandledPatternError,
    config_from_subscript,
    split_case_return
)


class Hello:
    def __init__(self, greeting):
        self.greeting = greeting


class Unhandled:
    def __repr__(self):
        return 'Unhandled'


def test_single_pattern():
    @pattern
    def pat(val):
        meta[match: val]  # noqa: F821

        ~ 'dale' | "DALE"
        ~ 'list' | []
        ~ str | val
        ~ int | 'int'+str(val)
        ~ Hello | val.greeting
        ~ default | 'default_' + str(val)  # noqa: F821

    obj = Hello("Welcome Friend")
    assert pat(obj) == "Welcome Friend"
    assert pat('dale') == "DALE"
    assert pat('some_string') == "some_string"
    assert pat(101) == "int101"
    assert pat('list') == []
    assert pat(Unhandled()) == 'default_Unhandled'


def test_multi_return():
    @pattern
    def multi_return(x):
        meta[match: x]  # noqa: F821

        ~ float | type(x), x, x
        ~ int | type(x), x

    assert multi_return(1) == (int, 1)
    assert multi_return(1.1) == (float, 1.1, 1.1)


def test_when():
    @pattern
    def multi_return(x):
        meta[match: x]  # noqa: F821

        ~ float [when: x > 1] | type(x), x, x  # noqa: F821, E211
        ~ int [when: x > 100 and x < 150] | x, 'Between 100 and 150'  # noqa: F821, E211, E501
        ~ int [when: x > 10] | 'INT OVER 10'   # noqa: F821, E211
        ~ int | type(x), x

    assert multi_return(1) == (int, 1)
    assert multi_return(11) == "INT OVER 10"
    assert multi_return(122) == (122, "Between 100 and 150")
    assert multi_return(1.1) == (float, 1.1, 1.1)
    with pytest.raises(UnhandledPatternError):
        assert multi_return(0.1) == (float, 1.1, 1.1)


def test_config_from_subscript():
    node = quick_parse("bob[match: x]").value
    meta = config_from_subscript(node)
    assert meta['match'][0].id == 'x'
    assert Counter(list(meta)) == Counter(['match'])

    node = quick_parse("bob[match: x, second: 1]").value
    meta = config_from_subscript(node)
    assert meta['match'][0].id == 'x'
    assert meta['second'][0].n == 1
    assert Counter(list(meta)) == Counter(['match', 'second'])

    node = quick_parse("bob[match: x, y, second: 1]").value
    meta = config_from_subscript(node)
    assert meta['match'][0].id == 'x'
    assert meta['match'][1].id == 'y'
    assert meta['second'][0].n == 1
    assert Counter(list(meta)) == Counter(['match', 'second'])


def test_split_case_return():
    node = quick_parse("~ x | type(x), y").value
    case_nodes, return_nodes = split_case_return(node)
    assert len(case_nodes) == 1
    assert len(return_nodes) == 2


def test_multi_pattern():
    @pattern
    def multi(x, y):
        meta[match: x, y]  # noqa: F821

        ~ float, 3 | type(x), x, y
        ~ int, 3 | type(x), x, 'int'
        ~ int, int | 'INT'

    assert multi(1, 2) == 'INT'
    assert multi(1, 3) == (int, 1, 'int')
    assert multi(1.0, 3) == (float, 1, 3)


def test_pattern_match_doc():
    # should ignore doc string.
    @pattern
    def docstring(x, y):
        """
        doc string
        """
        meta[match: x, y]  # noqa: F821


_missing = object()


def test_pattern_match_object():
    # test again object() sentinels

    @pattern
    def match(x):
        meta[match: x]  # noqa: F821

        ~ _missing | "MISSING"
        ~ default | x  # noqa: F821

    assert match(_missing) == "MISSING"
    assert match(100) == 100

    @pattern
    def multimatch(x, y):
        meta[match: x, y]  # noqa: F821

        ~ 1, _missing | x, "MISSING"
        ~ default | x, y  # noqa: F821

    assert multimatch(1, _missing) == (1, "MISSING")
    assert multimatch(_missing, 100) == (_missing, 100)
