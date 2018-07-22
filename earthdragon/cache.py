import collections

CACHE = {}

class staticcache:
    orig_func = None

    def __init__(self, func):
        if func:
            self.set_func(func)
        self.cache = {}

    def __call__(self, *args, **kwargs):
        func = self.orig_func
        ns = self.ns

        if not isinstance(args, collections.Hashable):
            print('not cacheable')
            # uncacheable. a list, for instance.
            # better to not cache than blow up.
            return func(*args, **kwargs)

        key = hash(args)
        if key in CACHE.setdefault(ns, {}):
            return CACHE[ns][key]

        ret = func(*args, **kwargs)
        CACHE[ns][key] = ret
        return ret

    def set_func(self, func):
        if self.orig_func:
            raise Exception("func already set")
        assert callable(func), "must wrap callable"

        func_name = func.__name__
        module = func.__module__
        ns = f'{module}.{func_name}'
        self.orig_func = func
        self.ns = ns
