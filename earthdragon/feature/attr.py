from earthdragon.class_util import get_unbounded_super
from earthdragon.multidecorator import MultiDecorator

# TODO make this lockable
class Attr:
    """
    Represents a MultiDecorator that is meant to wrap the attr name it is
    assigned to.

    This could have just been a simple wrapper and handled by a metaclass,
    but Features have the mandate of working by themselves. So a lot
    of the Attr logic is support that constraint.

    Usage 1:
        ```
        __init__ = Attr()
        __init__.add_hook(hook)
        ```

        When you don't have a concrete implementation but want to add a
        hook, pipeline, or transform.

        Note, we don't know which attribute name this Attr represents until
        `__get__`. We get the attribute name at runtime by checking
        obj.__class__.__dict__.

    Usage 2:
        ```
        @Attr
        def __init__(self):
            pass
        __init__.add_hook(hook)
        ```
    """
    def __init__(self, func=None):
        if func is None:
            decorator = MultiDecorator()
        elif isinstance(func, MultiDecorator):
            decorator = func.copy()
        elif callable(func):
            # @Attr
            # def method(self): pass
            decorator = MultiDecorator(func)
        else:
            raise TypeError("func must be None or Callable")
        self.decorator = decorator

        if isinstance(func, Attr):
            self.update(func)

    def update(self, other):
        assert isinstance(other, Attr)
        self.decorator.update(other.decorator)

    def __getattr__(self, name):
        passthrough = {
            'hooks', 'pipelines', 'transforms',
            'add_hook', 'add_pipeline', 'add_transform',
            'orig_func'
        }
        if name in passthrough:
            return getattr(self.decorator, name)
        raise AttributeError(name)

    def __get__(self, obj, cls=None):
        if obj is None:
            return self

        if self.decorator.orig_func is None:
            # Usage 2.
            orig_func = self._find_func(obj)
            self.set_func(orig_func)
        return self.decorator.__get__(obj)

    def set_func(self, func):
        self.decorator = self.decorator(func)

    def _find_func(self, obj):
        """
        Grab base func represented by this Attibute and bind it to
        MultiDecorator
        """
        # get unbound
        owner, base_func = get_unbounded_super(obj, self)
        if isinstance(base_func, Attr):
            base_func = base_func._find_func(owner)

        if isinstance(base_func, MultiDecorator):
            base_func = base_func.orig_func

        return base_func

    @classmethod
    def combine(cls, *attrs):
        """
        Take a list of attrs and merge them into a new Attr. It is assumed
        that the ordering is from base -> leaf so the last function is used
        as the Attr.func
        """
        decorators = [attr.decorator for attr in attrs]
        deco = MultiDecorator.combine(*decorators)
        return cls(deco)
