from collections import OrderedDict, defaultdict
from itertools import groupby
import nose.tools as nt

from ..attr import Attr
from ..anchor import (
    AnchorFunc,
    hook,
    pipeline,
    transform,
    add_to_attr,
    aggregate_anchor_funcs,
    AnchorFuncError,
    AnchorMeta
)

def test_add_to_attr():
    @hook('hello')
    def fake_hook():
        yield

    hello = Attr()
    add_to_attr(hello, fake_hook)
    nt.assert_is(hello.hooks[0], fake_hook.func)


@hook('hello')
def hello_hook(): yield

@hook('hello')
def hello_hook2(): yield

@hook('api_method')
def api_hook(): yield

api_method = lambda x: x

def test_aggregate_anchor_func():
    dct = OrderedDict()
    dct['hello_hook'] = hello_hook
    dct['hello_hook2'] = hello_hook2
    dct['api_method'] = Attr(api_method)
    dct['api_hook'] = api_hook

    update = aggregate_anchor_funcs(dct)
    nt.assert_is_instance(update['hello'], Attr)
    nt.assert_is_instance(update['api_method'], Attr)

    attr = update['hello']
    nt.assert_is(attr.orig_func, None)
    nt.assert_list_equal(attr.hooks, [hello_hook.func, hello_hook2.func])

    attr = update['api_method']
    nt.assert_is(attr.orig_func, api_method)
    nt.assert_list_equal(attr.hooks, [api_hook.func])

def test_aggregate_anchor_func_error():
    dct = OrderedDict()
    dct['api_hook'] = api_hook
    dct['api_method'] = Attr(api_method)

    with nt.assert_raises(AnchorFuncError):
        update = aggregate_anchor_funcs(dct)


def test_anchor_meta():
    class Blah(metaclass=AnchorMeta):
        __init__ = Attr()

        @Attr
        def shout(self, msg):
            return msg

    class Blah2(Blah):
        @Attr
        def __init__(self, bob):
            self.bob = 1
            self.logs = []

        @hook('shout')
        def log(self, msg):
            self.logs.append(msg)
            yield

    class Blah3(Blah2):
        @hook('shout')
        def log3(self, msg):
            self.logs.append(msg+'2')
            yield

        @hook('__init__')
        def init_log(self, *args):
            self.init_args = list(args)
            yield


    b3 = Blah3(3)
    nt.assert_list_equal(b3.init_args, [3])
    b3.shout('hi')
    nt.assert_list_equal(b3.logs, ['hi', 'hi2'])
    nt.assert_list_equal(b3.shout.hooks, [Blah2.log.func, Blah3.log3.func])
