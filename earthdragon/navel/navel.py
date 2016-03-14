from ..feature import FeatureBase, features, FeatureMeta
from .lockable import Lockable
from ..typelet import Typelet, gather_typelets, typelet_repr

class NavelMeta(FeatureMeta):
    def __new__(cls, name, bases, dct):
        return super().__new__(cls, name, bases, dct)

@features(Lockable)
class Navel(FeatureBase, metaclass=FeatureMeta):
    pass
