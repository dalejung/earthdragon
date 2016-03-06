import types
import inspect
from inspect import classify_class_attrs, getclosurevars

from .func_util import replace_class_closure

def init_name(mixin):
    return '__init_{mixin_name}'.format(mixin_name=mixin.__name__)

def class_attrs(cls):
    """
    Returns a dict of 
    {
        attr_name : dict of inspect.Attribute,
    }
    excluding any attribute inherited from object.
    """
    attrs = classify_class_attrs(cls)
    not_object_defined = lambda attr: attr.defining_class != object
    non_object_attrs = filter(not_object_defined, attrs)
    class_attr_dict = {}
    for attr in non_object_attrs:
        attr_dict = {name: getattr(attr, name) for name in attr._fields}
        class_attr_dict[attr.name] = attr_dict
    return class_attr_dict

def get_bindable(obj, base):
    """
    attr : dict of inspect.Attribute
    base : type

    Returns a obj/function that can properly be moved to another
    class. Largely this deals with Python 3 and super() binding
    the class via a closure.
    """
    if not isinstance(obj, types.FunctionType):
        return obj

    closurevars = getclosurevars(obj)
    if '__class__' in closurevars.nonlocals:
        obj = replace_class_closure(obj, base)
    return obj

def set_class_attr(base, name, attr):
    """
    attr : dict of inspect.Attribute
    base : type
    """
    obj = get_bindable(attr, base)
    setattr(base, name, obj)

def _get_name(obj, attr):
    """
    From a attr object, we want to find what it's attribute name is.
    We search the class definitions.
    """
    # obj can be instance or class
    cls = inspect.isclass(obj) and obj or obj.__class__
    # unwrap methods to get original func
    attr = isinstance(attr, types.MethodType) and attr.__func__ or attr
    for class_ in cls.__mro__:
        classdict = class_.__dict__
        for k,v in classdict.items():
            if v is attr:
                return k
    raise Exception("Could not find name for attr {attr}".format(attr=str(attr)))

def get_unbounded_super(obj, method):
    """
    obj : object
    method : callable, str
        Internally we want the leaf class's method and attr_name right away. We
        can derive both by either a method/func object or an attr name.


    obj_method : Direct method of object. Does not follow MRO.

    Given an object and method, we find the method it is shadowing. This has an
    extra bit of logic where it will skip ancestors that are the same value.

    So if you copy a method two a parent and child, will skip parent and look
    at grandparent.
    """
    cls = obj
    if not isinstance(cls, type):
        cls = obj.__class__

    if isinstance(method, str):
        name = method
        obj_method = cls.__dict__.get(method)
    else:
        name = _get_name(obj, method)
        obj_method = isinstance(method, types.MethodType) and method.__func__ or method

    for base in cls.mro()[1:]:
        super_method = getattr(base, name, None)
        if super_method is not obj_method and super_method is not None:
            break
    return base, super_method

