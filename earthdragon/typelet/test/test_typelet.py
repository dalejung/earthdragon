import unittest

import pytest

from ..typelet import (
        Int,
        List,
        Dict,
        TypeletError,
        KeyTypeError,
        Float,
        Unicode,
        _missing
)
from .. import util
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
        with pytest.raises(TypeletError):
            ex = ExampleObj()
            ex.dct = []

        ex = ExampleObj()
        ex.dct = {'int1': 123, 3: 123}
        self.assertCountEqual(ex.dct, ['int1', 3])

        with pytest.raises(TypeletError):
            ex.dct = {'int1': 123, 'float1': 1.1}

    def test_keyclass(self):
        with pytest.raises(KeyTypeError):
            ex = ExampleObj()
            ex.dct_key = {'int1': 123, 3: 123}


class ListTestCase(unittest.TestCase):
    def test_validate(self):
        with pytest.raises(TypeletError):
            ex = ExampleObj()
            ex.lst = {}

        ex = ExampleObj()
        ex.lst = [V(), V()]

        with pytest.raises(TypeletError):
            ex.lst = [V(), V(), 3]


class IntTestCase(unittest.TestCase):
    def test_default(self):
        obj = ExampleObj()
        assert obj.num == 10
        # default still goes through normal validation
        with pytest.raises(TypeletError):
            class BadDefault:
                bad_num = Int(default='10')


class FloatTestCase(unittest.TestCase):
    def test_validate(self):
        obj = ExampleObj()
        obj.fl = 0.133
        obj.fl = 10
        obj.fl = 1.3
        with pytest.raises(TypeletError):
            obj.fl = "DALE"


class TypeletTestCase(unittest.TestCase):
    def test_typelet_meta(self):
        class Parent(metaclass=TypeletMeta):
            parent_int = Int()

        class Child(Parent):
            child_int = Int()

        class GrandChild(Child):
            gc_int = Int()
            gc_float = Float()

        p = Parent()
        self.assertCountEqual(
            p._earthdragon_merged_typelets.keys(),
            ['parent_int']
        )

        # child should have both parent and child typelets
        c = Child()
        self.assertCountEqual(
            c._earthdragon_merged_typelets.keys(),
            ['child_int', 'parent_int']
        )
        self.assertCountEqual(
            c._earthdragon_typelets.keys(),
            ['child_int']
        )

        gc = GrandChild()
        self.assertCountEqual(
            gc._earthdragon_merged_typelets.keys(),
            ['child_int', 'parent_int', 'gc_int', 'gc_float']
        )
        self.assertCountEqual(
            gc._earthdragon_typelets.keys(),
            ['gc_int', 'gc_float']
        )


class InflateObj(metaclass=TypeletMeta):
    dct = Dict(int)
    fl = Float()
    num = Int(default=10)
    num2 = Int()


def test_inflate_kwargs():
    obj = InflateObj()
    state = {'fl': 1.1, 'dct': {'test': 1}, 'num': 1}
    inflate(obj, [], state, require_all=False)
    assert obj.fl == 1.1
    assert obj.dct == state['dct']
    assert obj.num == 1
    assert obj.num2 is None


def test_inflate_already_filled():
    # testing when keyword tries to fill in something filled by *args
    obj = InflateObj()
    state = {'fl': 1.1, 'dct': {'test': 1}}
    with pytest.raises(InvalidInitInvocation, match="Already filled in"):
        inflate(obj, [{'first': 2}], state, require_all=False)


def test_inflate_args():
    obj = InflateObj()
    args = [{'hi': 123}, 1.3]
    with pytest.raises(InvalidInitInvocation, match="Need to fill all args"):
        inflate(obj, args, {}, require_all=True)

    inflate(obj, args, {}, require_all=False)
    assert obj.fl == 1.3
    assert obj.num2 is None

    with pytest.raises(InvalidInitInvocation, match="Passed too many"):
        too_many_args = [{'hi': 123}, 1.3, 11, 13, 'too many']
        inflate(obj, too_many_args, {}, require_all=False)


def test_inflate_in_class():
    class InflateParentClass(metaclass=TypeletMeta):
        blah = Int(required=True)

    class InflateClass(InflateParentClass):
        """
        Class that passes through only typelets and requires all
        """

        id = Int(rquired=True)
        name = Unicode()

        def __init__(self, *args, **kwargs):
            inflate(self, args, kwargs, require_all=True)

    obj = InflateClass(id=1, name="Dale")
    assert obj.name == 'Dale'
    assert obj.id == 1

    # pass in wrong type
    with pytest.raises(TypeletError):
        obj = InflateClass(id=1.1, name="Dale")

    with pytest.raises(InvalidInitInvocation, match="Need to fill all args"):
        obj = InflateClass(name="Dale")

    # we only inflate current class typelets and not ancestors
    with pytest.raises(InvalidInitInvocation, match="Pass non typelet"):
        obj = InflateClass(id=1, name="Dale", blah=123)

    assert 'blah' in InflateClass._earthdragon_merged_typelets


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
    assert obj.id == 13
    assert obj.name is None
    assert obj.balance is None

    obj.balance = 1
    assert obj.balance == 1


def test_required():
    class InflateRequired(metaclass=TypeletMeta):
        """
        Class that passes through only typelets and requires all
        """

        id = Int(required=True)
        name = Unicode(required=True)
        age = Int()
        maiden_name = Unicode()

        def __init__(self, *args, **kwargs):
            inflate(self, args, kwargs)

    with pytest.raises(InvalidInitInvocation, match="All required typelets"):
        obj = InflateRequired(id=1)

    obj = InflateRequired(id=1, name="Dale")
    assert obj.name == 'Dale'


def test_inherited_inflate():
    """
    First pass on how to support inherited Typelets.

    The most sane world would be where Typelets are only
    defined on the current class.
    """
    class Parent(metaclass=TypeletMeta):
        p_id = Int(default=-1)

        def __init__(self, *args, **kwargs):
            inflate(self, args, kwargs, typelets_only=False, cls=__class__)
            super().__init__()

    class Child(Parent):
        c_id = Int(required=True)
        c_age = Int()

        def __init__(self, c_id, c_age=_missing, *args, **kwargs):
            inflate(self, [c_id, c_age], {}, typelets_only=False,
                    cls=__class__)
            super().__init__(*args, **kwargs)

    class GrandChild(Child):
        gc_id = Int(required=True)
        gc_name = Unicode(required=True)

        def __init__(self, g_id, gc_name, *args, **kwargs):
            inflate(self, [g_id, gc_name], {}, typelets_only=False)
            super().__init__(*args, **kwargs)

    gc = GrandChild(1, 'Dale', 123)
    assert gc.gc_id == 1
    assert gc.gc_name == 'Dale'
    assert gc.c_id == 123
    assert gc.p_id == -1
