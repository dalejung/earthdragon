from ..feature import FeatureBase, features, FeatureMeta
from .lockable import Lockable
from ..typelet import Typelet, gather_typelets, typelet_repr

class NavelMeta(FeatureMeta):
    def __new__(cls, name, bases, dct):
        if bases:
            typelets = gather_typelets(dct, bases)
            dct['_earthdragon_typelets'] = typelets
        return super().__new__(cls, name, bases, dct)

@features(Lockable)
class Navel(FeatureBase, metaclass=FeatureMeta):
    pass
