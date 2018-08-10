from asttools import (
    func_rewrite,
    func_code,
    Matcher,
    quick_parse,
    unwrap,
)

from nose.tools import (
    assert_equal,
    assert_raises,
    assert_count_equal
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
        meta[match: val]

        ~ 'dale' | "DALE"
        ~ 'list' | []
        ~ str | val
        ~ int | 'int'+str(val)
        ~ Hello | val.greeting
        ~ default | 'default_' + str(val)

    obj = Hello("Welcome Friend")
    assert_equal(pat(obj), "Welcome Friend")
    assert_equal(pat('dale'), "DALE")
    assert_equal(pat('some_string'), "some_string")
    assert_equal(pat(101), "int101")
    assert_equal(pat('list'), [])
    assert_equal(pat(Unhandled()), 'default_Unhandled')


def test_multi_return():
    @pattern
    def multi_return(x):
        meta[match: x]

        ~ float | type(x), x, x
        ~ int | type(x), x

    assert_equal(multi_return(1), (int, 1))
    assert_equal(multi_return(1.1), (float, 1.1, 1.1))


def test_when():
    @pattern
    def multi_return(x):
        meta[match: x]

        ~ float [when: x > 1] | type(x), x, x
        ~ int [when: x > 100 and x < 150] | x, 'Between 100 and 150'
        ~ int [when: x > 10]| 'INT OVER 10'
        ~ int | type(x), x

    assert_equal(multi_return(1), (int, 1))
    assert_equal(multi_return(11), "INT OVER 10")
    assert_equal(multi_return(122), (122, "Between 100 and 150"))
    assert_equal(multi_return(1.1), (float, 1.1, 1.1))
    with assert_raises(UnhandledPatternError):
        assert_equal(multi_return(0.1), (float, 1.1, 1.1))


def test_config_from_subscript():
    node = quick_parse("bob[match: x]").value
    meta = config_from_subscript(node)
    assert_equal(meta['match'][0].id, 'x')
    assert_count_equal(meta, ['match'])

    node = quick_parse("bob[match: x, second: 1]").value
    meta = config_from_subscript(node)
    assert_equal(meta['match'][0].id, 'x')
    assert_equal(meta['second'][0].n, 1)
    assert_count_equal(meta, ['match', 'second'])

    node = quick_parse("bob[match: x, y, second: 1]").value
    meta = config_from_subscript(node)
    assert_equal(meta['match'][0].id, 'x')
    assert_equal(meta['match'][1].id, 'y')
    assert_equal(meta['second'][0].n, 1)
    assert_count_equal(meta, ['match', 'second'])


def test_split_case_return():
    node = quick_parse("~ x | type(x), y").value
    case_nodes, return_nodes = split_case_return(node)
    assert_equal(len(case_nodes), 1)
    assert_equal(len(return_nodes), 2)


def test_multi_pattern():
    @pattern
    def multi(x, y):
        meta[match: x, y]

        ~ float, 3 | type(x), x, y
        ~ int, 3 | type(x), x, 'int'
        ~ int, int | 'INT'

    assert_equal(multi(1, 2), 'INT')
    assert_equal(multi(1, 3), (int, 1, 'int'))
    assert_equal(multi(1.0, 3), (float, 1, 3))


def test_pattern_match_doc():
    # should ignore doc string.
    @pattern
    def docstring(x, y):
        """
        doc string
        """
        meta[match: x, y]


_missing = object()


def test_pattern_match_object():
    # test again object() sentinels

    @pattern
    def match(x):
        meta[match: x]

        ~ _missing | "MISSING"
        ~ default | x

    assert_equal(match(_missing), "MISSING")
    assert_equal(match(100), 100)

    @pattern
    def multimatch(x, y):
        meta[match: x, y]

        ~ 1, _missing | x, "MISSING"
        ~ default | x, y

    assert_equal(multimatch(1, _missing), (1, "MISSING"))
    assert_equal(multimatch(_missing, 100), (_missing, 100))
