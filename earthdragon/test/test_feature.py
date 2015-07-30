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
    @features(Lockable)
    class NoInit(metaclass=FeatureMeta):
        pass

