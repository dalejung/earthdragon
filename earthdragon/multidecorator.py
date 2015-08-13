import abc
import functools
import inspect
import types

from toolz import compose
from .func_util import FunctionCategory
from .context import section
from .pattern_match import pattern

class DuplicateWrapperError(Exception):
    pass

class RequiredSelfError(Exception):
    def __init__(self, hook):
        msg = "{hook} expected a method call".format(hook=repr(hook))
        super().__init__(msg)

with section("Hook Paramter Categories"):
    class first(FunctionCategory):
        pass

    class system(FunctionCategory):
        """
        Denotes a system or platform hook. The only real change is that
        these hooks are meant to exist in all MultiDecorators within a certain
        context and should ignore unique constraint.
        """

    class static(FunctionCategory):
        pass

    class require_self(FunctionCategory):
        pass

    class nullary(FunctionCategory):
        pass

    class only_self(FunctionCategory):
        pass

    # TODO: Add decorator that sends additional meta info during hook priming.
    # Information like the current object, the func name, etc.

@pattern
def munge_args(hook, is_method, args, kwargs):
    meta [match : hook]

    ~ nullary | (), {}
    ~ static [when: is_method] | args[1:], kwargs
    ~ only_self | args[:1], {}
    ~ default | args, kwargs

@pattern
def hook_validate(hook, is_method, args, kwargs):
    meta [match : hook]

    ~ require_self [when: not is_method] | RequiredSelfError(hook)
    ~ only_self [when: not is_method] | RequiredSelfError(hook)
    ~ default | None

class MultiDecorator:
    """
    This largely comes from the realization that:

    @wrapper
    def some_func():
        pass

    is not granular enough. When wrapping functions I've found three main
    reasons:

    hook:
        pre and post execution hooks. wrapped function executes unadultered.
    transform:
        return a new function to execute. an example would be an LLVM compiler
        like numba.
    pipeline:
        function that takes the output of the func and return a new output.

    The delineation of hook from transform/pipeline is the most important as
    the order of decoration does not matter. Hook pre/post hooks will always
    run before and after pipeline. The only time you will need to care about
    decoration order is if you add multiple functions of the same type. But
    it should be easier to reason about that ordering.
    """
    orig_func = None

    def __init__(self, func=None):
        if func:
            self.set_func(func)
        self.obj = None
        self.hooks = []
        self.transforms = []
        self.pipelines = []

    def set_func(self, func):
        if self.orig_func:
            raise Exception("func already set")
        assert callable(func), "must wrap callable"
        self.orig_func = func
        self._update_func_meta(func)

    def _update_func_meta(self, func):
        for attr in functools.WRAPPER_ASSIGNMENTS:
            try:
                value = getattr(func, attr)
            except AttributeError:
                pass
            else:
                setattr(self, attr, value)

    _func = None
    @property
    def func(self):
        if self.orig_func is None:
            return None

        if self._func is None:
            func = self.orig_func
            for transform in self.transforms:
                func = transform(func)
            self._func = func
        return self._func

    def add_hook(self, hook):
        assert inspect.isgeneratorfunction(hook), \
                ("Hook needs to be a function with a single yield")
        self._add_func(hook, 'hook')
        self.sort_hooks()

    def sort_hooks(self):
        self.hooks.sort(key=lambda x: isinstance(x, first), reverse=True)

    def add_transform(self, transform):
        self._func = None # unset func cache
        self._add_func(transform, 'transform')

    _pipeline = None
    @property
    def pipeline(self):
        if self._pipeline is None:
            self._pipeline = compose(*self.pipelines[::-1])
        return self._pipeline

    def add_pipeline(self, pipeline):
        self._pipeline = None
        self._add_func(pipeline, 'pipeline')


    def _prime_hooks(self, __is_method, args, kwargs):
        """
        """
        def _prime_hook(hook, is_method, args, kwargs):
            err = hook_validate(hook, is_method, args, kwargs)
            if err:
                raise err

            args, kwargs = munge_args(hook, is_method, args, kwargs)
            return hook(*args, **kwargs)

        _hooks = []
        for hook in self.hooks:
            gen = _prime_hook(hook, __is_method, args, kwargs)
            _hooks.append(gen)
        return _hooks

    def __call__(self, *args, **kwargs):
        """ this is for non-method calls """
        return self.call(False, *args, **kwargs)

    def call(self, __is_method, *args, **kwargs):
        """
        """
        if self.func is None:
            new_dec = self.__class__(args[0])
            new_dec.update(self)
            return new_dec

        _hooks = self._prime_hooks(__is_method, args, kwargs)

        for _hook in _hooks:
            next(_hook, None)

        # pipeline
        ret = self.func(*args, **kwargs)
        ret = self.pipeline(ret)

        # do post hooks in reverse order
        for hook in _hooks[::-1]:
            try:
                # post hooks might someday need more data.
                context = None
                hook.send((ret, context))
            except StopIteration:
                pass

        return ret

    def update(self, other):
        for type_ in ['hooks', 'transforms', 'pipelines']:
            self_funcs = getattr(self, type_)
            other_funcs = getattr(other, type_)
            duplicate = set(self_funcs) & set(other_funcs)
            adder = getattr(self, 'add_{typ}'.format(typ=type_[:-1]))
            for func in other_funcs:
                adder(func)

        self.sort_hooks()

    def _add_func(self, func, kind):
        assert kind in ['hook', 'pipeline', 'transform']
        existing = getattr(self, kind + 's')
        duplicate = func in existing
        system_type = isinstance(func, system)
        if duplicate and not system_type:
            # because ordering might be important, we error here
            # till we find out how it should be handled.
            raise DuplicateWrapperError("Attempted to add existing func")
        if duplicate and system_type:
            # already have system hook, do nothing
            return

        existing.append(func)

    # act like a method
    def __get__(self, obj, cls=None):
        if obj is None:
            return self
        return MethodDecorator(self, obj)

    def __repr__(self):
        class_name = self.__class__.__name__
        func_name = self.func and self.__name__ or 'None'
        return "{class_name}({func_name})".format(**locals())

    @classmethod
    def combine(cls, *decos):
        """
        Take a list of decs and merge them into a new Attr. It is assumed
        that the ordering is from base -> leaf so the last function is used
        as the Attr.func
        """
        new_deco = cls()
        last_func = None
        for deco in decos:
            if deco.orig_func:
                last_func = deco.orig_func
            new_deco.update(deco)

        if last_func:
            new_deco.set_func(last_func)
        return new_deco

    def copy(self):
        return self.combine(self)

class CallWrapOnce:
    """
    Simple context wrapper that ensures that we only call hooks on the
    first call. We assume that super().method() means to only call
    the original function and not the wrapper.

    Imagine a method call count wrapper. We wouldn't want to increment the
    count for every super().method() call. Conceptually, we treat obj.method()
    as one call, even if it calls many super methods within its invocation
    """
    # TODO perf test this and many bring it to cython
    _in_flight = set()

    def __init__(self, key):
        self.key = key
        self.first_call = self.key not in CallWrapOnce._in_flight

    def __enter__(self):
        if self.first_call:
            CallWrapOnce._in_flight.add(self.key) # no op if already in
        return self.first_call

    def __exit__(self, type, value, traceback):
        if self.first_call:
            CallWrapOnce._in_flight.remove(self.key)

class MethodDecorator:
    """
    Acts like types.MethodType wrapper. We need MultiDecorator
    to know whether it's being called as method or regular
    function.
    """

    def __init__(self, decorator, obj):
        self.decorator = decorator
        self.obj = obj

    def __call__(self, *args, **kwargs):
        name = self.decorator.__name__
        key = (id(self.obj), name)
        with CallWrapOnce(key) as first_call:
            if first_call:
                # run the normal hooks
                return self.decorator.call(True, self.obj, *args, **kwargs)
            return self.decorator.orig_func(self.obj, *args, **kwargs)

    def __getattr__(self, name):
        if hasattr(self.decorator, name):
            return getattr(self.decorator, name)
        raise AttributeError(name)

    def __repr__(self):
        return "{decorator} bounded to {obj}".format(decorator=repr(self.decorator),
                                                     obj=repr(self.obj))
