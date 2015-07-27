import inspect
import types

from toolz import compose

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

class DuplicateWrapperError(Exception):
    pass

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
    def __init__(self, func=None):
        self.orig_func = func
        self.obj = None
        self.hooks = []
        self.transforms = []
        self.pipelines = []

    _func = None
    @property
    def func(self):
        if self._func is None:
            func = self.orig_func
            for transform in self.transforms:
                func = transform(func)
            self._func = func
        return self._func

    def add_hook(self, hook):
        assert inspect.isgeneratorfunction(hook), ("Hook needs to be a"
        "function with a single yield")
        self.hooks.append(hook)

    def add_transform(self, transform):
        self._func = None # unset func cache
        self.transforms.append(transform)
        self.func # force generation of func

    _pipeline = None
    @property
    def pipeline(self):
        if self._pipeline is None:
            self._pipeline = compose(*self.pipelines[::-1])
        return self._pipeline

    def add_pipeline(self, pipeline):
        self._pipeline = None
        self.pipelines.append(pipeline)

    def __call__(self, *args, **kwargs):
        if self.func is None:
            new_dec = self.__class__(args[0])
            new_dec.update(self)
            return new_dec

        # this is a method. pass along self
        if self.obj:
            args = list(args)
            args.insert(0, self.obj)

        _hooks = [hook(*args) for hook in self.hooks]
        for hook in _hooks:
            next(hook, None)

        # pipeline
        ret = self.func(*args, **kwargs)
        ret = self.pipeline(ret)

        for hook in _hooks:
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
            if duplicate:
                # because ordering might be important, we error here
                # till we find out how it should be handled.
                raise DuplicateWrapperError("Attempted to add existing func")
            self_funcs.extend(other_funcs)


    def __get__(self, obj, cls=None):
        self.obj = obj
        return self
