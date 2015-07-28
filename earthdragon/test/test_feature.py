from earthdragon.typelet import Bool
from earthdragon.function import MultiDecorator, require_self, static, only_self

from .. import feature
import imp;imp.reload(feature)
features = feature.features
FeatureMeta = feature.FeatureMeta
Attribute = feature.Attribute

class UnexpectedMutationError(Exception):
    pass

class Lockable:

    _locked = Bool()

    @only_self
    def unlock(self):
        self._locked = False
        yield
        self._locked = True


    __init__ = Attribute(MultiDecorator())
    __init__.add_hook(unlock)


    @require_self
    def _lock_check(self, name, value): # replicate setattr signature
        if name in ['_locked']:
            return

        if self._locked:
            raise UnexpectedMutationError(name)
        yield

    __setattr__ = Attribute(MultiDecorator())
    __setattr__.add_hook(_lock_check)



mutate = MultiDecorator()
mutate.add_hook(Lockable.unlock)

@features(Lockable)
class Something(metaclass=FeatureMeta):
    def __init__(self, bob):
        self.bob = bob

    @mutate
    def change_bob(self, bob):
        self.bob = bob


s = Something(1)
s = Something(1)

obj = s
name = '__init__'
super_method = getattr(super(obj.__class__, obj.__class__), name)
# get the unbound function from method-wrapper
base_func = getattr(super_method.__objclass__, name)
