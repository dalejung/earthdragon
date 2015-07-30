from .class_util import class_attrs, set_class_attr, init_name
from .multidecorator import MultiDecorator, only_self
from .func_util import get_unbounded_super
from .typelet import _get_name

"""
1. create features decorator with Features
2. Run FeatureMeta
"""

class Attr:
    """
    Represents a MultiDecorator that is meant to wrap the attr name it is
    assigned to.

    This could have just been a simple wrapper and handled by a metaclass,
    but Features have the mandate of working by themselves. So a lot
    of the Attr logic is support that constraint.

    Usage 1:
        ```
        __init__ = Attr()
        __init__.add_hook(hook)
        ```

        When you don't have a concrete implementation but want to add a
        hook, pipeline, or transform.

        Note, we don't know which attribute name this Attr represents until
        `__get__`. We get the attribute name at runtime by checking
        obj.__class__.__dict__.

    Usage 2:
        ```
        @Attr
        def __init__(self):
            pass
        __init__.add_hook(hook)
        ```
    """
    def __init__(self, func=None):
        if func is None:
            decorator = MultiDecorator()
        elif callable(func):
            # @Attr
            # def method(self): pass
            decorator = MultiDecorator(func)
        else:
            raise TypeError("func must be None or Callable")
        self.decorator = decorator
        self.func = None

    def __get__(self, obj, cls=None):
        if obj is None:
            return self

        if self.decorator.orig_func is None:
            # Usage 2.
            orig_func = self.find_func(obj)
            self.decorator = self.decorator(orig_func)
        return self.decorator.__get__(obj)

    def find_func(self, obj):
        """
        Grab base func represented by this Attibute and bind it to 
        MultiDecorator
        """
        name = _get_name(self, obj)
        # get unbound 
        base_func = get_unbounded_super(obj, name)
        return base_func

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
    _features_ = getattr(base, '_features_', [])[:] # copy so we don't modify ancestor
    if feature in _features_:
        msg = '{feature_name} already mixed'.format(feature_name=feature_name.__name__)
        print(msg)
        return False

    _features_.append(feature)
    mix_feature(base, feature)
    setattr(base, '_features_', _features_)

def mix_feature(base, feature):
    attrs = class_attrs(feature)
    base_attrs = class_attrs(base)

    feature_init = attrs.pop('__init__', None) # handled via setup_base_init above
    base_init = base_attrs.get('__init__', None)
    base_init_dec = base_init['object']
    assert isinstance(base_init_dec, MultiDecorator), 'should have been added via metaclass'
    if feature_init:
        if isinstance(feature_init['object'], (Attr, MultiDecorator)):
            feature_init_object = feature_init['object']
            base_init_dec.update(feature_init_object)
            feature_init['object'] = feature_init_object.orig_func

        attrs[init_name(feature)] = feature_init

    # need non closured function. messed up super
    for key, attr in attrs.items():
        # assuming dunder data objects are python meta attrs
        # this can be wrong. Maybe detect against base object and skip
        # data objects that are the same?
        if key.startswith('__') and key.endswith('__') and attr['kind'] == 'data':
            continue

        if key in base_attrs:
            raise featureInvariantError("Cannot duplicate attrs names with features")

        set_class_attr(base, key, attr)
