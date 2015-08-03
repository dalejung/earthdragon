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

def test_no_init_class():

    @features(BareFeature)
    class NoInit(metaclass=FeatureMeta):
        pass

class BareFeature:
    @first
    @only_self
    def init_hook(self):
        self.whee = 1
        yield

    __init__ = Attr()
    __init__.add_hook(init_hook)

class Parent(BareFeature):
    pass

#p = Parent()
