import inspect
import types
import gc
import collections

from typing import Union, Callable, Any

from .typecheck import typecheck


try:
    get_argspec = inspect.getfullargspec
    argspec_type = inspect.FullArgSpec
except AttributeError:
    get_argspec = inspect.getargspec
    argspec_type = inspect.ArgSpec


class SetOnceDict(collections.MutableMapping):

    def __init__(self):
        self._scope = {}

    def __delitem__(self, key):
        return self._scope.__delitem__(key)

    def __len__(self, key):
        return self._scope.__len__(key)

    def __getitem__(self, key):
        return self._scope.__getitem__(key)

    def __iter__(self):
        return self._scope.__iter__()

    def __setitem__(self, key, value):
        if key in self._scope:
            raise KeyError(f"{key} has already been set")
        self._scope.__setitem__(key, value)

    def update(self, *args, **kwargs):
        # copy logic of builtin dict
        for dct in args:
            if hasattr(dct, 'keys'):
                for k in dct:
                    self[k] = dct[k]
            else:
                for k, v in dct.items():
                    self[k] = v

        for k in kwargs:
            self[k] = kwargs[k]

    def __repr__(self):
        return 'Scope:' + repr(self._scope)


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


@typecheck
def get_invoked_args(argspec: Union[argspec_type, Callable[..., Any]],
                     *args, **kwargs):
    """
    Based on a functions argspec, figure out what the resultant function
    scope would be based on variables passed in
    """
    if not isinstance(argspec, argspec_type):
        # handle functools.wraps functions
        if hasattr(argspec, '__wrapped__'):
            argspec = get_argspec(argspec.__wrapped__)
        else:
            argspec = get_argspec(argspec)

    # we're assuming self is not in *args for method calls
    args_names = argspec.args
    if argspec.args[0] == 'self':
        args_names = args_names[1:]

    scope = SetOnceDict()
    # consume the (a, b, c) portion
    realized_args = dict(zip(args_names, args))
    scope.update(realized_args)

    if len(args) > len(args_names) and argspec.varargs is None:
        raise TypeError("too many positional arguments")

    # fill in kw args
    for k in list(kwargs.keys()):
        if k in args_names:
            scope[k] = kwargs.pop(k)

    # fill in the args default
    if len(args_names) > len(args):
        default_args = dict(
            zip(
                reversed(args_names),
                reversed(argspec.defaults)
            )
        )
        for k in default_args:
            if k not in scope:
                scope[k] = default_args[k]

    # leftover args into starargs
    if argspec.varargs is not None:
        # put the remaining args in *args
        varargs_name = argspec.varargs
        varargs_value = tuple(args[len(args_names):])
        scope[varargs_name] = varargs_value

    # kwonly
    for kwonly_name in argspec.kwonlyargs:
        if kwonly_name in kwargs:
            scope[kwonly_name] = kwargs.pop(kwonly_name)
        else:
            scope[kwonly_name] = argspec.kwonlydefaults[kwonly_name]

    # we have leftover keyword args. we need a **varkw
    if len(kwargs) > 0:
        if argspec.varkw:
            scope[argspec.varkw] = kwargs
        else:
            raise TypeError(f"got unexpected keyword arguments {list(kwargs)}")

    return scope

def invoker(a, b, *args, c=3, **kwargs):
    return a, b, c

print(inspect.getfullargspec(invoker))
invoked_args = get_invoked_args(invoker, 1, 2, 3, c=4, d=5)
correct_vals = {
    'a': 1, 'b': 2, 'c': 4, 'args': (3,), 'kwargs': {'d': 5}
}
print(correct_vals)
print(invoked_args._scope)

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
    funcs = [
        f for f in gc.get_referrers(code)
        if inspect.isfunction(f)
    ]

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
