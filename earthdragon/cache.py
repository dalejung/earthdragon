import collections

def get_func_ns(func):
    func_name = func.__name__
    module = func.__module__
    ns = f'{module}.{func_name}'
    return ns

class MemoryCache:
    pass

class staticcache:
    orig_func = None
    cache = {}

    def __init__(self, func=None, **kwargs):
        if func:
            self.set_func(func)
        self.config = kwargs

    def __call__(self, *args, **kwargs):
        if not self.orig_func:
            self.set_func(args[0])
            return self

        func = self.orig_func
        ns = self.ns

        key = self.get_cache_key(*args, **kwargs)

        if key in self.cache.setdefault(ns, {}):
            return self.cache[ns][key]

        ret = func(*args, **kwargs)

        if key is not None:
            self.cache[ns][key] = ret
        return ret

    def get_cache_key(self, *args, **kwargs):
        is_single = self.config.get('single', False)

        if is_single:
            return 'default'

        if not isinstance(args, collections.Hashable):
            return None

        print(args)
        key = hash(args)
        return key

    def set_func(self, func):
        if self.orig_func:
            raise Exception("func already set")
        assert callable(func), "must wrap callable"

        self.orig_func = func
        ns = get_func_ns(func)
        self.ns = ns
