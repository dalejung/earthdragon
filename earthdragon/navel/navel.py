from ..feature import FeatureBase, features, FeatureMeta
from .lockable import Lockable

class NavelMeta(FeatureMeta):
    pass

@features(Lockable)
class Navel(FeatureBase, metaclass=FeatureMeta):
    pass
