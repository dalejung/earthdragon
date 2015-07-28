from .classy import class_attrs, get_source_object, init_name
from .function import MultiDecorator, only_self

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
