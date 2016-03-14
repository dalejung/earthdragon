"""
Type checking primitives. Traits is an overloaded term. Came up with Typelets
ala IPython Traitlets.
"""
from collections import deque
import inspect
import uuid
import inspect
import datetime
import numbers

from ..class_util import _get_name

class TypeletError(Exception):
    pass

class KeyTypeError(TypeletError):
    pass

class TypeletMissing:
    pass
_missing = TypeletMissing()

class Typelet:
    def __init__(self, **kwargs):
        self.value = None
        self.name = None
        # TODO think about 1. should Typelet know about whether it's required
        # since it doesn't know when the obj it's on is initialized.
        # 2. Should this be hardcoded here or have a general kwargs system
        # for random metadata
        self.unique = kwargs.pop('unique', False)
        self.required = kwargs.pop('required', False)

        default = None
        if 'default' in kwargs:
            default = kwargs.pop('default')
            self.validate(default)
        self.default = default

    def __get__(self, obj, cls=None):
        if obj is None:
            obj = cls
        name = self.get_name(obj)
        return obj.__dict__.get(name, self.default)

    def __set__(self, obj, value):
        new_value = self._validate(obj, value)
        name = self.get_name(obj)
        obj.__dict__[name] = new_value

    def get_name(self, obj):
        if self.name is None:
            self.name = _get_name(obj, self)
        return self.name

    def _validate(self, obj, value):
        try:
            value = self.validate(value)
        except TypeletError as err:
            raise err # pass through typelet errors we handle
        except Exception as err:
            self.error(value, obj)

        return value

    def validate(self, value):
        return value

    def error(self, value, obj=None):
        class_name = type(self).__name__
        value_name = type(value).__name__
        msg = "TypeletError: Required {class_name}. Got {value_name}".format(**locals())
        raise TypeletError(msg)

class Unicode(Typelet):
    def validate(self, value):
        if isinstance(value, str):
            return value
        self.error(value)

class Int(Typelet):
    def __init__(self, min=None, max=None, **kwargs):
        self.min = min
        self.max = max
        super().__init__(**kwargs)

    def check_min(self, value):
        if self.min is None:
            return True
        return self.min <= value

    def check_max(self, value):
        if self.max is None:
            return True
        return self.max >= value

    def validate(self, value):
        if isinstance(value, int) and self.check_min(value)\
            and self.check_max(value):
            return value
        self.error(value)

class Float(Typelet):
    def validate(self, value):
        if isinstance(value, numbers.Number):
            return value
        self.error(value)

class Bool(Typelet):
    def validate(self, value):
        if isinstance(value, bool):
            return value
        self.error(value)

class UUID(Typelet):
    def validate(self, value):
        if isinstance(value, uuid.UUID):
            return value
        self.error(value)

class Datetime(Typelet):
    def validate(self, value):
        if isinstance(value, datetime.datetime):
            return value
        self.error(value)

class Type(Typelet):
    def __init__(self, _class, **kwargs):
        self.check_class = _class
        super().__init__(**kwargs)

    def validate(self, value):
        if isinstance(value, self.check_class):
            return value
        self.error(value)

def grab_class_reference(obj, class_name):
    """ Grab class ref from the module that object is defined in """
    modname = obj.__class__.__module__
    import sys
    mod = sys.modules[modname]
    check_class = getattr(mod, class_name, None)
    return check_class

class Collection(Typelet):

    # TODO replace list with a type checking list
    container_class = list

    def __init__(self, _class, **kwargs):
        self._class = _class
        self.check_class = None
        if inspect.isclass(_class):
            self.check_class = _class
        super().__init__(**kwargs)

    def _check_container_class(self, value):
        if not isinstance(value, self.container_class):
            raise TypeletError("Must be a {container_class}".format(
                container_class=str(self.container_class)
            ))

    def _check_collection_values(self, values):
        check_class = self.check_class
        for v in values:
            if not isinstance(v, check_class):
                raise TypeletError("Collection can only contain {type}")

    def values(self, obj):
        return obj

    def _validate(self, obj, value):
        if self.check_class is None:
            self.check_class = grab_class_reference(obj, self._class)
        return super()._validate(obj, value)

    def validate(self, value):
        self._check_container_class(value)
        self._check_collection_values(self.values(value))
        return value

class List(Collection):
    container_class = list

class Deque(Collection):
    container_class = deque

class Dict(Collection):
    container_class = dict

    def __init__(self, _class, **kwargs):
        self.key_class = kwargs.pop('key_class', None)
        super().__init__(_class, **kwargs)

    def values(self, obj):
        return obj.values()

    def _validate_keys(self, value):
        if self.key_class is None:
            return
        for k in value:
            if not isinstance(k, self.key_class):
                raise KeyTypeError("Keys must be {type} type".format(
                    type=str(self.key_class)
                ))

    def validate(self, value):
        value = super().validate(value)
        self._validate_keys(value)
        return value
