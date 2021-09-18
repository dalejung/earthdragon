import pytest

from ..navel import Navel, NavelMeta
from ...feature import Attr
from ..lockable import UnexpectedMutationError, mutate
from earthdragon.typelet import TypeletMeta, Int


def test_navel_lockable():
    class Hippo(Navel):
        def __init__(self, x, y):
            self.x = x
            self.y = y

        def bad_change_x(self, x):
            self.x = x

        @mutate
        def good_change_x(self, x):
            self.x = x

    hip = Hippo(3, 10)
    assert hip.x == 3
    assert hip.y == 10
    with pytest.raises(UnexpectedMutationError):
        hip.x = 30

    # unchanged
    assert hip.x == 3

    with pytest.raises(UnexpectedMutationError):
        hip.bad_change_x(10)

    # unchanged
    assert hip.x == 3

    # huzzah
    hip.good_change_x(100)
    assert hip.x == 100

    class HippoKid(Hippo):
        @mutate
        def good_change_x(self, x):
            self.x = x + 1

    hk = HippoKid(100, 200)
    hk.good_change_x(49)
    assert hk.x == 50


def test_nested_lockable():

    class Parent(Navel):
        def __init__(self, x, y):
            self.x = x
            self.y = y

    class Child(Parent):
        def __init__(self, x, y):
            super().__init__(x, y)  # this was broken before
            self.x = x
            self.y = y

    c = Child(1, 2)  # noqa: F841


def test_hooks_called_once():
    count = 0

    def transform(func):
        nonlocal count
        count += 1
        assert func is not object.__init__
        return func

    class Parent(Navel):
        __init__ = Attr()
        __init__.add_transform(transform)

    class Child(Parent):
        def __init__(self):
            super().__init__()

    c = Child()  # noqa: F841
    assert count == 1


def test_multiple_meta():
    class TestMultiMeta(NavelMeta, TypeletMeta):
        pass

    class Hippo(metaclass=TestMultiMeta):
        x = Int()
        y = Int()

        def __init__(self, x, y):
            self.x = x
            self.y = y

    class HippoChild(Hippo):
        pass

    h = HippoChild(1, 2)  # noqa: F841
