import sys

class TracerRunner(object):
    """
    """
    def __init__(self):
        self.tracers = []

    def __enter__(self):
        sys.settrace(self.trace_dispatch)
        return self

    def __exit__(self, type, value, traceback):
        sys.settrace(None)

    def add_tracer(self, tracer):
        self.tracers.append(tracer)

    def trace_dispatch(self, frame, event, arg):
        dispatch = None
        for tracer in self.tracers:
            # last one wins
            dispatch = tracer(frame, event, arg)
        return dispatch

class Tracer:
    def __call__(self, frame, event, arg):
        meth = getattr(self, 'trace_'+ event, self.trace_default)
        return meth(frame, event, arg)

    def trace_default(self, frame, event, arg):
        return None

class FuncTracer(Tracer):

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

    def trace_call(self, frame, event, arg):
        f_code = frame.f_code
        if f_code not in self.codemap:
            return self

        meta = self.codemap.get(f_code)
        f_locals = frame.f_locals
        self._execute_callback(f_locals, meta)
        return None

    def _execute_callback(self, f_locals, meta):
        callback = meta.get('callback')
        if callback:
            callback(meta['name'], f_locals)

        if self.global_callback:
            self.global_callback(meta['name'], f_locals)

class Builder:
    def __init__(self):
        self.runner = TracerRunner()

    def funcs(self, *args, **kwargs):
        func_tracer = FuncTracer(*args, **kwargs)
        self.runner.add_tracer(func_tracer)
        return self

    def tracer(self, tracer):
        self.runner.add_tracer(tracer)
        return self

    def __enter__(self):
        return self.runner.__enter__()

    def __exit__(self, *args, **kwargs):
        return self.runner.__exit__(*args, **kwargs)

def trace(*args, **kwargs):
    builder = Builder()
    # default to func tracer
    builder.funcs(*args, **kwargs)
    return builder
