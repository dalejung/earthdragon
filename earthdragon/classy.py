from functools import wraps, reduce
from inspect import classify_class_attrs


class MixinInvariantError(Exception):
    pass

def class_attrs(cls):
    attrs = classify_class_attrs(cls)
    not_object_defined = lambda attr: attr.defining_class != object
    non_object_attrs = filter(not_object_defined, attrs)
    class_attr_dict = dict((attr.name, attr) for attr in non_object_attrs)
    return class_attr_dict

def setup_base_init(init):
    if hasattr(init, '__ed_init__'):
        return init

    @wraps(init)
    def _wrapped_init(self, *args, **kwargs):
        init(self, *args, **kwargs)
        for mixin in self._mixins_:
            mixin.__init__(self)
    _wrapped_init.__ed_init__ = True
    return _wrapped_init

def ensure_init_uniqueness(mixins):
    mixin_dicts = {mixin: mixin().__dict__ for mixin in mixins}
    def no_duplicate(dct1, dct2):
        if set(dct1) & set(dct2):
            raise MixinInvariantError("Mixin inits cannot set intersecting attributes")
        return set(dct1) | set(dct2)
    reduce(no_duplicate, mixin_dicts.values())

def mix(base, mixin):
    """
    Parameters
    ----------
    base : Component Class
    mixin : Class

    Note:
        The mixin.__init__ is called at the end of BaseComponent.__init__.
    """
    mixin_name =  mixin.__name__
    _mixins_ = getattr(base, '_mixins_', [])[:] # copy so we don't modify ancestor
    if mixin_name in _mixins_:
        print(('{mixin_name} already mixed'.format(mixin_name=mixin_name)))
        return False

    _mixins_.append(mixin)

    base_init = base.__init__
    base.__init__ = setup_base_init(base_init)

    ensure_init_uniqueness(_mixins_)

    attrs = class_attrs(mixin)
    attrs.pop('__init__', None) # handled via setup_base_init above
    base_attrs = class_attrs(base)

    mixed = []
    for key, attr in attrs.items():
        # assuming dunder data objects are python meta attrs
        # this can be wrong. Maybe detect against base object and skip
        # data objects that are the same?
        if key.startswith('__') and key.endswith('__') and attr.kind == 'data':
            continue

        if key in base_attrs:
            raise MixinInvariantError("Cannot duplicate attrs names with mixins")

        mixed.append(key)
        setattr(base, key, attr.object)

    setattr(base, '_mixins_', _mixins_)
