import nose.tools as nt

from ..navel import Navel
from ..lockable import UnexpectedMutationError, mutate

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
    nt.assert_equal(hip.x, 3)
    nt.assert_equal(hip.y, 10)
    with nt.assert_raises(UnexpectedMutationError):
        hip.x = 30
    # unchanged
    nt.assert_equal(hip.x, 3)


    with nt.assert_raises(UnexpectedMutationError):
        hip.bad_change_x(10)
    # unchanged
    nt.assert_equal(hip.x, 3)

    # huzzah
    hip.good_change_x(100)
    nt.assert_equal(hip.x, 100)

    class HippoKid(Hippo):
        @mutate
        def good_change_x(self, x):
            self.x = x +1

    hk = HippoKid(100, 200)
    hk.good_change_x(49)
    nt.assert_equal(hk.x, 50)

def test_nested_lockable():
    class Parent(Navel):
        def __init__(self, x, y):
            self.x = x
            self.y = y

    class Child(Parent):
        def __init__(self, x, y):
            super().__init__(x, y) # this was broken before
            self.x = x
            self.y = y

    c = Child(1, 2)
