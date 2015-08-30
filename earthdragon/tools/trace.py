import sys

class Trace(object):
    """
    """
    def __init__(self, *args, **kwargs):
        self.codemap = {}

        funcs = list(filter(callable, args))
        for func in funcs:
            self.add_function(func)

        self.global_callback = kwargs.get('callback')

    def add_function(self, func, callback=None):
        code = func.__code__
        meta = {}
        meta['callback'] = callback
        meta['name'] = func.__name__
        meta['qualname'] = func.__qualname__
        self.codemap[code] = meta

    def __enter__(self):
        sys.settrace(self.trace_dispatch)
        return self

    def __exit__(self, type, value, traceback):
        sys.settrace(None)

    def trace_dispatch(self, frame, event, arg):
        if event != 'call':
            return None

        f_code = frame.f_code
        if f_code not in self.codemap:
            return self.trace_dispatch

        meta = self.codemap.get(f_code)
        f_locals = frame.f_locals
        self._execute_callback(f_locals, meta)
        return self.trace_dispatch


    def _execute_callback(self, f_locals, meta):
        callback = meta.get('callback')
        if callback:
            callback(meta['name'], f_locals)

        if self.global_callback:
            self.global_callback(meta['name'], f_locals)

