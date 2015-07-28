from .classy import class_attrs, get_source_object, init_name
from .multidecorator import MultiDecorator, only_self
from .func_util import get_unbounded_super
from .typelet import _get_name

class Attribute:
    """
    Represents a MultiDecorator that is meant to wrap the attr name it is
    assigned to.

    This could have just been a simple wrapper and handled by a metaclass,
    but Features have the mandate of working by themselves. So a lot
    of the Attribute logic is support that constraint.
    """
    def __init__(self, decorator):
        self.decorator = decorator
        self.func = None

    def __get__(self, obj, cls=None):
        if self.func is None:
            self.func = self.generate_func(obj)
        return self.func

    def generate_func(self, obj):
        """
        Grab base func represented by this Attibute and bind it to 
        MultiDecorator
        """
        name = _get_name(self, obj)
        # get unbound 
        base_func = get_unbounded_super(obj, name)
        func = self.decorator(base_func)
        return func.__get__(obj)

    def __getattr__(self, name):
        if hasattr(self.decorator, name):
            return getattr(self.decorator, name)
        raise AttributeError(name)

class features:
    def __init__(self, *args):
        self.features = args

    def __call__(self, cls):
        mix(cls, self.features[0])
        return cls

class FeatureMeta(type):
    def __new__(cls, name, bases, dct):
        init = dct.get('__init__', None)
        if init:
            # using to expose lifecycle hooks for init
            new_init = MultiDecorator(init)
            new_init.add_hook(run_feature_inits)
            dct['__init__'] = new_init
        return super().__new__(cls, name, bases, dct)

@only_self
def run_feature_inits(self):
    yield
    # after main init. run the feature inits.
    for feature in self._features_:
        feature_init = getattr(self, init_name(feature), None)
        if feature_init:
            feature_init()

def mix(base, feature):
    """
    Parameters
    ----------
    base : Component Class
    feature : Class

    Note:
        The feature.__init__ is called at the end of BaseComponent.__init__.
    """
    feature_name =  feature.__name__
    _features_ = getattr(base, '_features_', [])[:] # copy so we don't modify ancestor
    if feature_name in _features_:
        print(('{feature_name} already mixed'.format(feature_name=feature_name)))
        return False

    _features_.append(feature)

    attrs = class_attrs(feature)
    feature_init = attrs.pop('__init__', None) # handled via setup_base_init above
    if feature_init:
        attrs[init_name(feature)] = feature_init
    base_attrs = class_attrs(base)

    mixed = []
    # need non closured function. messed up super
    for key, attr in attrs.items():
        # assuming dunder data objects are python meta attrs
        # this can be wrong. Maybe detect against base object and skip
        # data objects that are the same?
        if key.startswith('__') and key.endswith('__') and attr.kind == 'data':
            continue

        if key in base_attrs:
            raise featureInvariantError("Cannot duplicate attrs names with features")

        mixed.append(key)
        setattr(base, key, get_source_object(attr, base))

    setattr(base, '_features_', _features_)
