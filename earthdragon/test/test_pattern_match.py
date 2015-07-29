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

from ..pattern_match import pattern

class Hello:
    def __init__(self, greeting):
        self.greeting = greeting

class Unhandled:
    def __repr__(self):
        return 'Unhandled'

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

@pattern
def multi_return(x):
    meta[match: x]

    ~ int | type(x), x
    ~ float | type(x), x, x

nt.assert_equal(multi_return(1), (int, 1))
nt.assert_equal(multi_return(1.1), (float, 1.1, 1.1))
