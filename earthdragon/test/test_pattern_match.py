from asttools import (
    get_source,
    func_rewrite,
    func_code,
    Matcher,
    quick_parse,
    unwrap,
)
import ast
import copy
import inspect
import nose.tools as nt

from ..pattern_match import (
    pattern,
    UnhandledPatternError,
    config_from_subscript,
    split_case_return,
    split_case
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
    nt.assert_equal(pat(obj), "Welcome Friend")
    nt.assert_equal(pat('dale'), "DALE")
    nt.assert_equal(pat('some_string'), "some_string")
    nt.assert_equal(pat(101), "int101")
    nt.assert_equal(pat('list'), [])
    nt.assert_equal(pat(Unhandled()), 'default_Unhandled')

def test_multi_return():
    @pattern
    def multi_return(x):
        meta[match: x]

        ~ float | type(x), x, x
        ~ int | type(x), x

    nt.assert_equal(multi_return(1), (int, 1))
    nt.assert_equal(multi_return(1.1), (float, 1.1, 1.1))

def test_when():
    @pattern
    def multi_return(x):
        meta[match: x]

        ~ float [when: x > 1] | type(x), x, x
        ~ int [when: x > 100 and x < 150] | x, 'Between 100 and 150'
        ~ int [when: x > 10]| 'INT OVER 10'
        ~ int | type(x), x

    nt.assert_equal(multi_return(1), (int, 1))
    nt.assert_equal(multi_return(11), "INT OVER 10")
    nt.assert_equal(multi_return(122), (122, "Between 100 and 150"))
    nt.assert_equal(multi_return(1.1), (float, 1.1, 1.1))
    with nt.assert_raises(UnhandledPatternError):
        nt.assert_equal(multi_return(0.1), (float, 1.1, 1.1))

def test_config_from_subscript():
    node = quick_parse("bob[match: x]").value
    meta = config_from_subscript(node)
    nt.assert_equal(meta['match'][0].id, 'x')
    nt.assert_count_equal(meta, ['match'])

    node = quick_parse("bob[match: x, second: 1]").value
    meta = config_from_subscript(node)
    nt.assert_equal(meta['match'][0].id, 'x')
    nt.assert_equal(meta['second'][0].n, 1)
    nt.assert_count_equal(meta, ['match', 'second'])

    node = quick_parse("bob[match: x, y, second: 1]").value
    meta = config_from_subscript(node)
    nt.assert_equal(meta['match'][0].id, 'x')
    nt.assert_equal(meta['match'][1].id, 'y')
    nt.assert_equal(meta['second'][0].n, 1)
    nt.assert_count_equal(meta, ['match', 'second'])

def test_split_case_return():
    node = quick_parse("~ x | type(x), y").value
    case_nodes, return_nodes = split_case_return(node)
    nt.assert_equal(len(case_nodes), 1)
    nt.assert_equal(len(return_nodes), 2)

def test_multi_pattern():
    @pattern
    def multi(x, y):
        meta[match: x, y]

        ~ float, 3 | type(x), x, y
        ~ int, 3 | type(x), x, 'int'
        ~ int, int | 'INT'

    nt.assert_equal(multi(1, 2), 'INT')
    nt.assert_equal(multi(1, 3), (int, 1, 'int'))
    nt.assert_equal(multi(1.0, 3), (float, 1, 3))
