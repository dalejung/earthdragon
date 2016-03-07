"""
Utilities for integrating Typelet into classes.
"""
from collections import OrderedDict
from .typelet import Typelet

class TypeletMeta(type):
    """
    Metaclass that makes classes Typelet aware. The most important
    part is replacing the class dict with an OrderedDict so we retain
    the order that typelet are defined.
    """
    def __prepare__(name, bases):
        mdict = OrderedDict()
        return mdict

    def __new__(cls, name, bases, dct):
        typelets = gather_typelets(dct, bases)
        dct['_earthdragon_typelets'] = typelets
        return super().__new__(cls, name, bases, dct)

def _gather_typelets(dct, key='_earthdragon_typelets'):
    if key in dct:
        return dct[key]

    typelets = OrderedDict()
    for k, v in dct.items():
        if isinstance(v, Typelet):
            typelets[k] = v
    return typelets

def gather_typelets(dct, bases=[]):
    class_dicts = [base.__dict__ for base in bases] + [dct]
    typelet_dicts = map(_gather_typelets, class_dicts)

    typelets = OrderedDict()
    for tdict in typelet_dicts:
        typelets.update(tdict)
    return typelets

def typelet_repr(self, typelets=None):
    """
    Repr utility that will default to printing the
    class and its typelets
    """
    class_ = self.__class__
    class_name = class_.__name__

    attrs = typelets or []
    if hasattr(class_, '_earthdragon_typelets'):
        attrs = getattr(class_, '_earthdragon_typelets')
    if hasattr(class_, '__repr_attrs__'):
        attrs = getattr(class_, '__repr_attrs__')
    return _typelet_repr(self, attrs)

def _typelet_repr(self, attrs):
    class_ = self.__class__
    class_name = class_.__name__

    bits = []
    for k in attrs:
        v = getattr(self, k)
        bits.append("{k}={v}".format(k=k, v=v))
    attr_string = ', '.join(bits)
    return "{class_name}({attr_string})".format(**locals())


class InvalidInitInvocation(Exception):
    pass


def fill(obj, filled, name, value):
    if name in filled:
        raise InvalidInitInvocation("Already filled in '{name}'".format(name=name))
    setattr(obj, name, value)
    filled[name] = True


def inflate(self, args, kwargs, typelets_only=True, require_all=False):
    """
    Useful function within __init__ to match *args, **kwargs to typelet
    definition.

    typelets_only : bool
        Any variables passed in must match a typelet definition. If your
        init function takes in additional varialbes, you cannot pass them
        to inflate when this is True.
    require_all : bool
        Requires that typelet variables are set in one pass. Useful for
        immutable value objects.
    """
    filled = {}
    _typelets = self._earthdragon_typelets
    required_typelets = {name: typelet for name, typelet in _typelets.items()
            if typelet.required}

    if typelets_only and len(args) > len(_typelets):
        raise InvalidInitInvocation("Passed too many positional values")

    if typelets_only and not set(kwargs).issubset(_typelets):
        raise InvalidInitInvocation("Pass non typelet keyword arg")

    for arg, name in zip(args, _typelets):
        fill(self, filled, name, arg)

    for k, v in kwargs.items():
        fill(self, filled, k, v)

    if require_all and set(filled) != set(_typelets):
        raise InvalidInitInvocation("Need to fill all args")

    if set(filled) < set(required_typelets):
        raise InvalidInitInvocation("All required typelets must be passed in")
