from earthdragon.typelet import Bool
from earthdragon.function import MultiDecorator, require_self, static

from .. import feature
from ..typelet import _get_name
import imp;imp.reload(feature)
features = feature.features
FeatureMeta = feature.FeatureMeta

class UnexpectedMutationError(Exception):
    pass

class Attribute:
    """
    """
    def __init__(self, decorator):
        self.decorator = decorator
        self.func = None

    def __get__(self, obj, cls=None):
        if self.func is None:
            self.func = self.generate_func(obj)
        return self.func

    def generate_func(self, obj):
        name = _get_name(self, obj)
        super_method = getattr(super(obj.__class__), name)
        # get the unbound function from method-wrapper
        base_func = getattr(super_method.__objclass__, name)
        func = self.decorator(base_func)
        return func.__get__(obj)

    def __getattr__(self, name):
        if hasattr(self.decorator, name):
            return getattr(self.decorator, name)
        raise AttributeError(name)

class Lockable:

    _locked = Bool()

    def __init__(self):
        print('boo')
        self._locked = True

    @require_self
    def _lock_check(self, name, value): # replicate setattr signature
        if name in ['_locked']:
            return

        if self._locked:
            raise UnexpectedMutationError()
        yield

    __setattr__ = Attribute(MultiDecorator())
    __setattr__.add_hook(_lock_check)


    @static
    def unlock(self):
        self._locked = False
        yield
        self._locked = True

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
