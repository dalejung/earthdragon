import unittest

import nose.tools as nt

from ..typelet import Int, List, Dict, TypeletError, KeyTypeError, Float

class V:
    pass

class ExampleObj:
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
        import numpy as np
        obj = ExampleObj()
        obj.fl = np.float(1.9)
        obj.fl = 10
        obj.fl = 1.3
        with nt.assert_raises(TypeletError):
            obj.fl = "DALE"
