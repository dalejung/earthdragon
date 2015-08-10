"""
Meta tools for class construction.
"""
from collections import OrderedDict
import inspect
import ctypes

def reload_locals(frame):
    ctypes.pythonapi.PyFrame_LocalsToFast(ctypes.py_object(frame), ctypes.c_int(1))

class MetaDict(OrderedDict):
    def __init__(self, setitem_handler, *args, **kwargs):
        self.setitem_handler = setitem_handler
        self.classdict = ClassDict(self)
        super().__init__(*args, **kwargs)

    def __setitem__(self, key, value):
        super().__setitem__(key, value)

    def copy(self):
        return self.__class__(self.setitem_handler, self)


class ClassDict:
    """ simple obj to limit interface to MetaDict """
    def __init__(self, dct):
        self.dct = dct

    def __setitem__(self, key, value):
        super(MetaDict, self.dct).__setitem__(key, value)

    def __getitem__(self, key):
        return self.dct[key]

    def __contains__(self, key):
        return key in self.dct

    def __delitem__(self, key):
        del self.dct[key]

    def keys(self):
        return self.dct.keys()

class MetaMeta(type):
    @classmethod
    def __prepare__(mcl, name, bases):
        mdict = MetaDict(mcl.setitem_handler)
        return mdict

    def setitem_handler(key, value, scope):
        return True

def mro(dct, bases, name):
    class_dicts = [base.__dict__ for base in bases] + [dct]
    for cdict in class_dicts:
        if name in cdict:
            return cdict[name]

def derived_methods(self):
    pass
    # TODO
    # it's a common idiom for a class to return attribute dynamic.
    # however these attributes are usually derived from some fixed
    # data like a list of columns or indexes.
    # so we should be able to more solidly define these items and also
    # easily add support with __dir__
