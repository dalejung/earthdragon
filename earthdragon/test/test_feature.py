from earthdragon.typelet import Bool
from earthdragon.multidecorator import (
    MultiDecorator,
    require_self,
    static,
    only_self,
    first
)

import nose.tools as nt
from .. import feature
import imp;imp.reload(feature)
features = feature.features
FeatureMeta = feature.FeatureMeta
Attr = feature.Attr

class UnexpectedMutationError(Exception):
    pass

class Lockable:

    _locked = Bool()

    @first
    @only_self
    def unlock(self):
        self._locked = False
        yield
        self._locked = True

    __init__ = Attr()
    __init__.add_hook(unlock)


    @first
    @require_self
    def _lock_check(self, name, value): # replicate setattr signature
        if name in ['_locked']:
            return

        if self._locked:
            raise UnexpectedMutationError(name)
        yield

    __setattr__ = Attr()
    __setattr__.add_hook(_lock_check)

mutate = MultiDecorator()
mutate.add_hook(Lockable.unlock)

@features(Lockable)
class Something(metaclass=FeatureMeta):
    def __init__(self, bob):
        self.bob = bob

    @mutate
    def change_bob(self, bob):
        self.bob = bob

    def bad(self, bob):
        self.bob = bob

@features(Lockable)
class Another(metaclass=FeatureMeta):
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
