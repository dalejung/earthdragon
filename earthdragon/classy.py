import types
from functools import wraps, reduce
from .func_util import replace_class_closure
from .class_util import class_attrs, get_bindable, init_name

class MixinInvariantError(Exception):
    pass

class MixinMeta(type):
    def __new__(cls, name, bases, dct):
        init = dct.get('__init__', None)
        if init:
            dct['__init__'] = setup_base_init(init)
        return super().__new__(cls, name, bases, dct)

def setup_base_init(init):
    if hasattr(init, '__ed_init__'):
        return init

    @wraps(init)
    def _wrapped_init(self, *args, **kwargs):
        base = init.__class__
        for mixin in self._mixins_:
            mixin_init = getattr(self, init_name(mixin), None)
            if mixin_init:
                mixin_init()
        init(self, *args, **kwargs)
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

    ensure_init_uniqueness(_mixins_)

    attrs = class_attrs(mixin)
    mixin_init = attrs.pop('__init__', None) # handled via setup_base_init above
    if mixin_init:
        attrs[init_name(mixin)] = mixin_init
    base_attrs = class_attrs(base)

    mixed = []
    # need non closured function. messed up super
    for key, attr in attrs.items():
        # assuming dunder data objects are python meta attrs
        # this can be wrong. Maybe detect against base object and skip
        # data objects that are the same?
        if key.startswith('__') and key.endswith('__') and attr['kind'] == 'data':
            continue

        if key in base_attrs:
            raise MixinInvariantError("Cannot duplicate attrs names with mixins")

        mixed.append(key)
        setattr(base, key, get_bindable(attr, base))

    setattr(base, '_mixins_', _mixins_)
