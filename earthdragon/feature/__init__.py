from ..class_util import class_attrs, set_class_attr, init_name
from ..multidecorator import MultiDecorator, only_self, system
from ..pattern_match import pattern
from .anchor import propogate_anchor

from .attr import Attr
from types import FunctionType

class features:
    def __init__(self, *args):
        self.features = args

    def __call__(self, cls):
        mix(cls, self.features[0])
        return cls

@system
@only_self
def run_feature_inits(self):
    yield
    # after main init. run the feature inits.
    for feature in self._features_:
        feature_init = getattr(self, init_name(feature), None)
        if feature_init:
            feature_init()

class FeatureMeta(type):
    def __new__(cls, name, bases, dct):
        preprocess = lambda parent, child: child.add_hook(run_feature_inits)
        new_init = propogate_anchor(dct, bases, '__init__', preprocess)
        dct['__init__'] = new_init
        return super().__new__(cls, name, bases, dct)

class Feature(metaclass=FeatureMeta):
    __init__ = Attr()

class FeatureInvariantError(Exception):
    pass

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
    assert isinstance(base_init_dec, (Attr)), 'should have been added via metaclass'
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
            raise FeatureInvariantError("Cannot duplicate attrs names with features")

        set_class_attr(base, key, attr)
