import pytest

from earthdragon.typelet import Bool
from earthdragon.multidecorator import (
    MultiDecorator,
    require_self,
    static,
    only_self,
    first
)

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
    assert ni.touched is True
    assert ni.init_feature == 13

    fi = FirstInit(1)
    assert fi.arg == 1
    assert fi.touched is True
    assert fi.init_feature == 13


def test_multiple_feature():

    @features(BareFeature)
    class NoInit(FeatureBase):
        pass

    @features(WootFeature)
    class MultipleFeature(NoInit):
        pass

    # should get it's own copy
    assert NoInit.__init__ is not MultipleFeature.__init__

    f = MultipleFeature()

    assert f.touched is True
    assert 'woot' in f.__dict__
    assert f.woot is True


def test_simple_init():
    """
    When an Attr is in parent and we just have a normal method, defining
    that method should just replace the orig_func.
    """
    class SimpleInit(FeatureBase):
        # a regualr method should just replace the original
        def __init__(self, hi):
            self.hi = hi

    assert SimpleInit.__init__.orig_func


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
    assert c.parent_init is True
    assert c.child_init is True
    # wrapper funcs called once
    assert count == 1
    assert EVENTS == [c]
