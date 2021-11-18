import types
import importlib


def reimport(obj):
    if isinstance(obj, (str, types.ModuleType)):
        module = reimport_module(obj)
        return module

    # return a reimported object
    if hasattr(obj, '__module__'):
        name = obj.__name__
        module = reimport_module(obj.__module__)
        return getattr(module, name)

    raise Exception(f"Don't know how to reimport {obj}")


def reimport_module(module):
    if isinstance(module, str):
        module = importlib.import_module(module)
    module = importlib.reload(module)
    return module
