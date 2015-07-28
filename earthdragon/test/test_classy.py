import unittest

import nose.tools as nt

from ..classy import mix, MixinInvariantError, MixinMeta

def test_mixin():
    class Bob(metaclass=MixinMeta):
        def __init__(self):
            self.bob = 1

    class BobMixin:
        def __init__(self):
            self.bobmix = 1

        def __getattr__(self, name):
            return 'hi'

    class BobMixin2:
        def  __init__(self):
            self.bobmix2 = 3

        def hello(self):
            return 'hi'

    mix(Bob, BobMixin)
    mix(Bob, BobMixin2)

    b = Bob()
    nt.assert_equal(b.bob, 1)
    nt.assert_equal(b.bobmix, 1)
    nt.assert_equal(b.bobmix2, 3)

def test_duplicate_init():

    class Bob:
        def __init__(self):
            self.bob = 1

    class DuplicateMixin:
        def __init__(self):
            self.dupe = 1

    class DuplicateMixin2:
        def __init__(self):
            self.dupe = 1

    mix(Bob, DuplicateMixin)
    with nt.assert_raises(MixinInvariantError):
        mix(Bob, DuplicateMixin2)

@unittest.expectedFailure
def test_duplicate_init_base():
    # currently we don't error if mixin conflicts with base __init__
    # this is because we enforce empty constructor for mixins, but not
    # bases. So we'd need to either raise an error on instantiation or
    # do some ast parsing to gather setters.
    raise NotImplementedError()

def test_duplicate_attrs():

    class Bob:
        def __init__(self):
            self.bob = 1

        def __setattr__(self, name, value):
            pass

    class DuplicateMixin:
        def __init__(self):
            self.dupe = 1

        def __setattr__(self, name, value):
            pass
    with nt.assert_raises(MixinInvariantError):
        mix(Bob, DuplicateMixin)
