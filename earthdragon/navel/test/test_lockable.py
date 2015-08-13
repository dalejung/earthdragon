import nose.tools as nt

from ..lockable import Lockable, mutate, UnexpectedMutationError
from earthdragon.feature import features, FeatureBase

@features(Lockable)
class Something(FeatureBase):
    def __init__(self, bob):
        self.bob = bob

    @mutate
    def change_bob(self, bob):
        self.bob = bob

    def bad(self, bob):
        self.bob = bob

@features(Lockable)
class Another(FeatureBase):
    def __init__(self, bob):
        self.bob = bob

    @mutate
    def change_bob(self, bob):
        self.bob = bob

    def bad(self, bob):
        self.bob = bob

def test_lockable():
    s = Something(1)
    s.change_bob(3)
    nt.assert_equal(s.bob, 3)
    with nt.assert_raises(UnexpectedMutationError):
        s.bad(10)

    with nt.assert_raises(UnexpectedMutationError):
        s.bob = 1

    a = Another('test')
    a.change_bob(33)
