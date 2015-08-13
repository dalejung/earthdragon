import nose.tools as nt

from ..lockable import Lockable, mutate, UnexpectedMutationError
from earthdragon.feature import features, FeatureBase

def test_lockable():
    @features(Lockable)
    class Something(FeatureBase):
        def __init__(self, bob):
            self.bob = bob

        @mutate
        def change_bob(self, bob):
            self.bob = bob

        def bad(self, bob):
            self.bob = bob
    s = Something(1)
    s.change_bob(3)
    nt.assert_equal(s.bob, 3)
    with nt.assert_raises(UnexpectedMutationError):
        s.bad(10)

    with nt.assert_raises(UnexpectedMutationError):
        s.bob = 1

def test_nested_lockable():
    """
    If we have nested unlocks, we have to use a counter and not a boolean.
    Unlock
        Unlock
        Lock
        # this stuff here SHOULD be unlocked but isn't due to the previous lock
    Lock
    """
    @features(Lockable)
    class Super(FeatureBase):
        def __init__(self, bob):
            super().__init__()
            self.bob = bob

    s = Super(1)
    with nt.assert_raises(UnexpectedMutationError):
        s.bob = 1
