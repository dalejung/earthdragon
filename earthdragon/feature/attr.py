from earthdragon.class_util import get_unbounded_super
from earthdragon.multidecorator import MultiDecorator

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
        if hasattr(self.decorator, name):
            return getattr(self.decorator, name)
        raise AttributeError(name)

    def __get__(self, obj, cls=None):
        if obj is None:
            return self

        if self.decorator.orig_func is None:
            # Usage 2.
            orig_func = self.find_func(obj)

            if isinstance(orig_func, Attr):
                orig_func = orig_func.func

            self.decorator = self.decorator(orig_func)
        return self.decorator.__get__(obj)

    def find_func(self, obj):
        """
        Grab base func represented by this Attibute and bind it to 
        MultiDecorator
        """
        # get unbound
        base_func = get_unbounded_super(obj, self)
        return base_func

