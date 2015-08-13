from ..feature import FeatureBase, features
from .lockable import Lockable

@features(Lockable)
class Navel(FeatureBase):
    pass
