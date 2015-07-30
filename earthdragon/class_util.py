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
    class_attr_dict = dict((attr.name, dict(attr.__dict__)) for attr in non_object_attrs)
    return class_attr_dict

def get_bindable(attr, base):
    """
    attr : dict of inspect.Attribute
    base : type

    Returns a obj/function that can properly be moved to another
    class. Largely this deals with Python 3 and super() binding
    the class via a closure.
    """
    obj = attr['object']
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
