import unittest

import nose.tools as nt

from ..typelet import (
        Int,
        List,
        Dict,
        TypeletError,
        KeyTypeError,
        Float,
        Unicode
)
from ..util import TypeletMeta, inflate, InvalidInitInvocation

class V:
    pass

class ExampleObj(metaclass=TypeletMeta):
    dct = Dict(int)
    dct_key = Dict(int, key_class=str)
    lst = List(V)
    num = Int(default=10)
    fl = Float()

class DictTestCase(unittest.TestCase):
    def test_validate(self):
        with nt.assert_raises(TypeletError):
            ex = ExampleObj()
            ex.dct = []

        ex = ExampleObj()
        ex.dct = {'int1': 123, 3: 123}
        nt.assert_count_equal(ex.dct, ['int1', 3])

        with nt.assert_raises(TypeletError):
            ex.dct = {'int1': 123, 'float1': 1.1}

    def test_keyclass(self):
        with nt.assert_raises(KeyTypeError):
            ex = ExampleObj()
            ex.dct_key = {'int1': 123, 3: 123}

class ListTestCase(unittest.TestCase):
    def test_validate(self):
        with nt.assert_raises(TypeletError):
            ex = ExampleObj()
            ex.lst = {}

        ex = ExampleObj()
        ex.lst = [V(), V()]

        with nt.assert_raises(TypeletError):
            ex.lst = [V(), V(), 3]

class IntTestCase(unittest.TestCase):
    def test_default(self):
        obj = ExampleObj()
        nt.assert_equal(obj.num, 10)
        # default still goes through normal validation
        with nt.assert_raises(TypeletError):
            class BadDefault:
                bad_num = Int(default='10')

class FloatTestCase(unittest.TestCase):
    def test_validate(self):
        obj = ExampleObj()
        obj.fl = 0.133
        obj.fl = 10
        obj.fl = 1.3
        with nt.assert_raises(TypeletError):
            obj.fl = "DALE"

def test_typelet_meta():
    class Parent(metaclass=TypeletMeta):
        parent_int = Int()

    class Child(Parent):
        child_int = Int()

    class GrandChild(Child):
        gc_int = Int()
        gc_float = Float()

    p = Parent()
    nt.assert_count_equal(p._earthdragon_typelets.keys(), ['parent_int'])

    # child should have both parent and child typelets
    c = Child()
    nt.assert_count_equal(c._earthdragon_typelets.keys(), ['child_int', 'parent_int'])

    gc = GrandChild()
    nt.assert_count_equal(gc._earthdragon_typelets.keys(),
            ['child_int', 'parent_int', 'gc_int', 'gc_float'])

class InflateObj(metaclass=TypeletMeta):
    dct = Dict(int)
    fl = Float()
    num = Int(default=10)
    num2 = Int()

def test_inflate_kwargs():
    obj = InflateObj()
    state = {'fl' : 1.1, 'dct': {'test':1}, 'num': 1}
    inflate(obj, [], state, require_all=False)
    nt.assert_equal(obj.fl, 1.1)
    nt.assert_equal(obj.dct, state['dct'])
    nt.assert_equal(obj.num, 1)
    nt.assert_is_none(obj.num2)

def test_inflate_already_filled():
    # testing when keyword tries to fill in something filled by *args
    obj = InflateObj()
    state = {'fl' : 1.1, 'dct': {'test':1}}
    with nt.assert_raises_regex(InvalidInitInvocation, "Already filled in"):
        inflate(obj, [{'first': 2}], state, require_all=False)

def test_inflate_args():
    obj = InflateObj()
    args = [{'hi': 123}, 1.3]
    with nt.assert_raises_regex(InvalidInitInvocation, "Need to fill all args"):
        inflate(obj, args, {}, require_all=True)

    inflate(obj, args, {}, require_all=False)
    nt.assert_equal(obj.fl, 1.3)
    nt.assert_is_none(obj.num2)

    with nt.assert_raises_regex(InvalidInitInvocation, "Passed too many"):
        too_many_args = [{'hi': 123}, 1.3, 11, 13, 'too many']
        inflate(obj, too_many_args, {}, require_all=False)


def test_inflate_in_class():
    class InflateClass(metaclass=TypeletMeta):
        """
        Class that passes through only typelets and requires all
        """

        id = Int()
        name = Unicode()

        def __init__(self, *args, **kwargs):
            inflate(self, args, kwargs)


    obj = InflateClass(id=1, name="Dale")
    nt.assert_equal(obj.name, 'Dale')
    nt.assert_equal(obj.id, 1) 

    # pass in wrong type
    with nt.assert_raises(TypeletError):
        obj = InflateClass(id=1.1, name="Dale")

    with nt.assert_raises_regex(InvalidInitInvocation, "Need to fill all args"):
        obj = InflateClass(name="Dale")


def test_inflate_in_class_loose():
    class InflateLooseClass(metaclass=TypeletMeta):
        """
        Test that infalte works on loose settings
        """

        id = Int()
        name = Unicode()
        balance = Float()

        def __init__(self, *args, **kwargs):
            inflate(self, args, kwargs, typelets_only=False, require_all=False)

    obj = InflateLooseClass(id=13)
    nt.assert_equal(obj.id, 13)
    nt.assert_is_none(obj.name)
    nt.assert_is_none(obj.balance)

    obj.balance = 1
    nt.assert_equal(obj.balance, 1)
