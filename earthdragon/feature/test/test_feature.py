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
from ..feature import *
from earthdragon.context import WithScope

class ns(WithScope):
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        super().__init__()

    def enter(self):
        for k, v in self.kwargs.items():
            self.scope[k] = v

        self.reload_locals()

def test_no_init_class():

    @features(BareFeature)
    class NoInit(metaclass=FeatureMeta):
        pass

class BareFeature:

    @only_self
    def touch_init(self):
        self.touched = True
        yield

    # what we are saying here is tht we want to wrap __init__
    # but we do not provide an init
    __init__ = Attr()
    __init__.add_hook(touch_init)

class WootFeature:

    @only_self
    def woot_init(self):
        self.woot = True
        yield

    __init__ = Attr()
    __init__.add_hook(woot_init)


@features(BareFeature)
class NoInit(metaclass=FeatureMeta):
    pass

@features(WootFeature)
class Frank(NoInit):
    pass

o = NoInit()
f = Frank()
