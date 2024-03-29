from collections.abc import Hashable
import types
import asyncio

from .func_util import get_invoked_args, get_func_ns


class MemoryCache:
    pass


class staticcache:
    orig_func = None

    # Note that this is shared across all staticcache instances and is
    # effectively global.
    # caches are partitioned by the function namespace. The reason for this
    # easier static caching when developing iteratively with a long running
    # kernel.
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

        # async
        # TODO what's the best way to dedupe the code when supporting
        # sync and async
        if asyncio.iscoroutinefunction(func):
            async def _wrap_coroutine():
                if key in self.cache.setdefault(ns, {}):
                    return self.cache[ns][key]

                coro = func(*args, **kwargs)
                ret = await coro
                if key is not None:
                    self.cache[ns][key] = ret
                return ret

            return _wrap_coroutine()

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

        invoked_args = get_invoked_args(self.orig_func, *args, **kwargs)

        if not isinstance(invoked_args, Hashable):
            return None

        try:
            key = hash(invoked_args)
        except TypeError:
            return None

        return key

    def set_func(self, func):
        if self.orig_func:
            raise Exception("func already set")
        assert callable(func), "must wrap callable"

        self.orig_func = func
        ns = get_func_ns(func)
        self.ns = ns

    def clear(self, *args, **kwargs):
        ns = self.ns
        if ns not in self.cache:
            return

        ns_cache = self.cache.get(ns)
        key = self.get_cache_key(*args, **kwargs)
        if key in ns_cache:
            del ns_cache[key]
