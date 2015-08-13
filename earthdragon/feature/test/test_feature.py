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
from ...feature import features, FeatureBase, Attr
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
    class NoInit(FeatureBase):
        pass

    @features(BareFeature)
    class FirstInit(FeatureBase):
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
    class NoInit(FeatureBase):
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
    class SimpleInit(FeatureBase):
        # a regualr method should just replace the original
        def __init__(self, hi):
            self.hi = hi

    nt.assert_true(SimpleInit.__init__.orig_func)

def test_hooks_called_once():
    count = 0
    def transform(func):
        nonlocal count
        count += 1
        assert func is not object.__init__
        return func

    EVENTS = []
    def hook(self):
        EVENTS.append(self)
        yield

    class Parent(FeatureBase):
        @Attr
        def __init__(self):
            self.parent_init = True
            super().__init__()
        __init__.add_transform(transform)
        __init__.add_hook(hook)


    class Child(Parent):
        def __init__(self):
            self.child_init = True
            super().__init__()

    c = Child()
    # both inits called
    nt.assert_true(c.parent_init)
    nt.assert_true(c.child_init)
    # wrapper funcs called once
    nt.assert_equal(count, 1)
    nt.assert_list_equal(EVENTS, [c])
