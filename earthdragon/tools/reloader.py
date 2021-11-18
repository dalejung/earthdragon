import sys
import types
import importlib
import inspect


def reimport(obj):
    """
    Reimport module.

    Can take in module path as a string so you can pre-reload the module.
    ```
    reimport("bob.subbob")
    from bob.subob import bob3
    ```
    """
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


def get_existing_module(module):
    if isinstance(module, types.ModuleType):
        module = module.__name__

    return sys.modules.get(module, None)


def reimport_ns(module, depth=1):
    """
    TODO: Basically want the ability to specify a module *after* import
    statements and have it search out and replace references that:

    1. Were defined in module
    2. Were imported from that module.

    So #2 is a bit open to how to accomplish. I could just check `module` attrs
    match any scope objects. That still isn't 100% since that won't track the
    exact `from mod import X` since we might've imported from a different
    module. Could also parse the python to find the references.
    """
    existing_module = get_existing_module(module)
    module = reimport_module(module)
    module_path = module.__name__

    frame = inspect.stack()[depth].frame
    scope = frame.f_locals

    direct_match = {}

    for k, v in scope.items():
        if getattr(v, '__module__', False) == module_path:
            direct_match[k] = getattr(module, k)
            continue
