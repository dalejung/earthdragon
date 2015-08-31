import inspect
import types
import gc

def make_cell(value):
    # http://nedbatchelder.com/blog/201301/byterun_and_making_cells.html
    # Construct an actual cell object by creating a closure right here,
    # and grabbing the cell object out of the function we create.
    return (lambda: value).__closure__[0]

def replace_class_closure(func, class_):
    """
    functions defined within classes that use super() are given
    a __class__ closure variable which is how the super() magic works.
    However, this messes up methods when they are attached to a diferent
    class.
    """
    closurevars = inspect.getclosurevars(func)
    assert '__class__' in closurevars.nonlocals

    new_func = types.FunctionType(func.__code__, func.__globals__,
                                closure=(make_cell(class_),))
    return new_func

def get_invoked_args(argspec, *args, **kwargs):
    """
    Based on a functions argspec, figure out what the resultant function
    scope would be based on variables passed in
    """
    if not isinstance(argspec, inspect.ArgSpec):
        # handle functools.wraps functions
        if hasattr(argspec, '__wrapped__'):
            argspec = inspect.getargspec(argspec.__wrapped__)
        else:
            argspec = inspect.getargspec(argspec)

    # we're assuming self is not in *args for method calls
    args_names = argspec.args
    if argspec.args[0] == 'self':
        args_names = args_names[1:]

    realized_args = dict(zip(args_names, args))
    assert not set(realized_args).intersection(kwargs)
    res = kwargs.copy()
    res.update(realized_args)
    return res

class CategoryMeta(type):
    def __new__(cls, name, bases, dct):
        dct.setdefault('_registry', set())
        dct['__new__'] = CategoryMeta.identity_register
        return super().__new__(cls, name, bases, dct)

    def identity_register(cls, func):
        """
        used for __new__. Instead of returning new instance we just register
        and return func.
        """
        func = inspect.unwrap(func)
        cls._registry.add(func)
        return func

    def __instancecheck__(cls, C):
        return C in cls._registry

class FunctionCategory(metaclass=CategoryMeta):
    pass

def get_parent(code):
    """
    Given a code object find the Class that uses it as a method.
    First we find the function that wraps the code, then from there
    we find the class dict or method object.

    Note: get_referrers will often return both forms. We escape on whatever we
    hit first.

    Also, this is a real slow function and relies on the gc.
    """
    funcs = [f for f in gc.get_referrers(code)
                    if inspect.isfunction(f)]

    if len(funcs) != 1:
        return None

    refs = [f for f in gc.get_referrers(funcs[0])]

    for ref in refs:
        # assume if that if a dict is pointed to by a class,
        # that dict is the __dict__
        if isinstance(ref, dict):
            parents = [p for p in gc.get_referrers(ref) if isinstance(p, type)]
            if len(parents) == 1:
                return parents[0].__name__

        if inspect.ismethod(ref):
            return ref.__qualname__.rsplit('.', 1)[0]

    return None
