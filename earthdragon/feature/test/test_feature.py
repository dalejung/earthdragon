from earthdragon.typelet import Bool
from earthdragon.multidecorator import (
    MultiDecorator,
    require_self,
    static,
    only_self,
    first
)

import nose.tools as nt
from ... import feature
from ...feature import *
from earthdragon.context import WithScope


class BareFeature:

    @Attr
    def __init__(self):
        self.init_feature = 13

    @only_self
    def touch_init(self):
        self.touched = True
        yield

    # what we are saying here is tht we want to wrap __init__
    # but we do nmot provide an init
    __init__.add_hook(touch_init)

class WootFeature:

    @only_self
    def woot_init(self):
        self.woot = True
        yield

    __init__ = Attr()
    __init__.add_hook(woot_init)

def test_feature():
    @features(BareFeature)
    class NoInit(Feature):
        pass

    @features(BareFeature)
    class FirstInit(Feature):
        def __init__(self, arg):
            self.arg = arg

    ni = NoInit()
    nt.assert_equal(ni.touched, True)
    nt.assert_equal(ni.init_feature, 13)

    fi = FirstInit(1)
    nt.assert_equal(fi.arg, 1)
    nt.assert_equal(fi.touched, True)
    nt.assert_equal(fi.init_feature, 13)

def test_multiple_feature():

    @features(BareFeature)
    class NoInit(Feature):
        pass

    @features(WootFeature)
    class MultipleFeature(NoInit):
        pass

    # should get it's own copy
    nt.assert_is_not(NoInit.__init__, MultipleFeature.__init__)

    f = MultipleFeature()

    nt.assert_equal(f.touched, True)
    nt.assert_in('woot', f.__dict__)
    nt.assert_equal(f.woot, True)


def test_simple_init():
    """
    When an Attr is in parent and we just have a normal method, defining
    that method should just replace the orig_func.
    """
class SimpleInit(Feature):
    # a regualr method should just replace the original
    def __init__(self, hi):
        self.hi = hi

nt.assert_true(SimpleInit.__init__.orig_func)
