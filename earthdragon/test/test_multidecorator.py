from ..multidecorator import (
    MultiDecorator,
    DuplicateWrapperError,
    require_self,
    static,
    nullary,
    only_self,
    RequiredSelfError,
)

import nose.tools as nt

def test_decorator():
    EVENTS = []
    @MultiDecorator
    def sup():
        EVENTS.append('sup')


    def cm():
        EVENTS.append('cm.pre')
        yield
        EVENTS.append('cm.post')

    def cm2():
        EVENTS.append('cm2.pre')
        yield
        EVENTS.append('cm2.post')

    sup.add_hook(cm)
    sup.add_hook(cm2)

    sup()
    nt.assert_list_equal(EVENTS, ['cm.pre', 'cm2.pre', 'sup', 'cm.post', 'cm2.post'])

def test_decorator_factory():
    EVENTS = []
    some_dec = MultiDecorator()
    def some_hook():
        EVENTS.append('pre')
        yield
        EVENTS.append('post')
    some_dec.add_hook(some_hook)

    @some_dec
    def whee():
        EVENTS.append('whee')

    whee()
    nt.assert_list_equal(EVENTS, ['pre', 'whee', 'post'])

def test_decorator_methods():
    EVENTS = []
    method_dec = MultiDecorator()
    def on_off(self, *args):
        self.on = True
        yield
        self.on = False
    method_dec.add_hook(on_off)

    class Example:
        def __init__(self):
            self.on = False

        @method_dec
        def hello(self, callback):
            nt.assert_true(self.on)
            callback(self)
            self.called = True
            print('whell')

    e = Example()
    nt.assert_false(e.on)
    e.hello(lambda s: s)
    nt.assert_false(e.on)
    nt.assert_true(e.called)

def test_pipeline():
    EVENTS = []
    def some_hook(*args):
        EVENTS.append('pre')
        yield
        EVENTS.append('post')

    def add_1(ret):
        EVENTS.append(1)
        return ret + [1]

    def add_2(ret):
        EVENTS.append(2)
        return ret + [2]

    func_dec = MultiDecorator()
    func_dec.add_hook(some_hook)
    func_dec.add_pipeline(add_1)
    func_dec.add_pipeline(add_2)

    @func_dec
    def duplicate(x):
        return [x, x]

    ret = duplicate('dale')

    # add_1 was added first. shoudl be exeucted first
    nt.assert_equal(EVENTS[1], 1)
    nt.assert_equal(EVENTS[2], 2)

    # orig func
    nt.assert_equal(ret[0], 'dale') 
    nt.assert_equal(ret[1], 'dale')
    # pipeline
    nt.assert_equal(ret[2], 1)
    nt.assert_equal(ret[3], 2)

def some_hook(*args):
    yield

def add_1(ret):
    return ret + [1]

def add_2(ret):
    return ret + [2]

def test_decorator_update():
    func_dec = MultiDecorator()
    func_dec.add_hook(some_hook)
    func_dec.add_pipeline(add_1)

    new_dec = MultiDecorator()
    new_dec.add_pipeline(add_2)
    new_dec.update(func_dec)
    # note that new functions will be added after
    nt.assert_list_equal(new_dec.pipelines, [add_2, add_1])
    nt.assert_list_equal(new_dec.hooks, [some_hook])

def test_decorator_update_duplicate():
    func_dec = MultiDecorator()
    func_dec.add_hook(some_hook)

    new_dec = MultiDecorator()
    new_dec.add_hook(some_hook)
    with nt.assert_raises(DuplicateWrapperError):
        new_dec.update(func_dec)

def test_decorator_send_ret():
    """
    The yield for a hook will return the function/pipeline return
    and a context object. context object is there for future proofing.
    """
    EVENTS = []
    def log_return(*args):
        ret, context = yield
        EVENTS.append(ret)


    func_dec = MultiDecorator()
    func_dec.add_hook(log_return)

    @func_dec
    def hello(val):
        return val + 1

    hello(100)
    nt.assert_equal(EVENTS[0], 101)


def test_hook_short_circuit():
    """
    Support having a return first in the generator, thus 
    shortcircuiting both pre and post hook behaviors.
    """
    def yield_return(bob):
        yield_return.events = []
        if bob > 10:
            return
        yield_return.events.append('pre')
        ret, context = yield
        yield_return.events.append('post')
        yield_return.events.append(ret)

    func_dec = MultiDecorator()
    func_dec.add_hook(yield_return)


    @func_dec
    def power(val):
        return val*val

    # normal
    ret = power(10)
    nt.assert_equal(ret, 100)
    nt.assert_list_equal(yield_return.events, ['pre', 'post', 100])

    # hit the short circuit
    ret = power(11)
    nt.assert_equal(ret, 121)
    nt.assert_list_equal(yield_return.events, [])

def test_hook_nullary():
    """
    @nullary marks function as 0 arity.
    """
    @require_self
    def counter(self, *args):
        self.count += 1
        yield

    EVENTS = []
    @nullary
    def log_greeting():
        EVENTS.append('log_greeting')
        yield

    method_dec = MultiDecorator()
    method_dec.add_hook(counter)
    method_dec.add_hook(log_greeting)

    class Greeter:
        def __init__(self):
            self.count = 0

        @method_dec
        def hello(self, greeting='hello'):
            return greeting

    g = Greeter()
    g.hello('sup')
    nt.assert_equal(g.count, 1)

    nt.assert_list_equal(EVENTS, ['log_greeting'])


    # test on non-method function
    EVENTS = []
    @nullary
    def log_pre_post():
        EVENTS.append('log_greeting')
        ret, context = yield
        EVENTS.append(ret)

    null_dec = MultiDecorator()
    null_dec.add_hook(log_pre_post)

    @null_dec
    def hello(greeting='hi'):
        return greeting


    hello('sup')
    nt.assert_list_equal(EVENTS, ['log_greeting', 'sup'])


    def bare():
        yield
    without_null_dec = MultiDecorator()
    without_null_dec.add_hook(bare)

    @without_null_dec
    def hello(greeting='hi'):
        return greeting

    # without nullary, we pass in unneeded params
    with nt.assert_raises_regex(TypeError, '0 positional arguments but 1 was'):
        hello('whee')

def test_hook_only_self():
    """
    @only_self should only get self
    """
    @only_self
    def counter(self):
        self.count += 1
        yield

    method_dec = MultiDecorator()
    method_dec.add_hook(counter)

    class Greeter:
        def __init__(self):
            self.count = 0

        @method_dec
        def hello(self, greeting='hello'):
            return greeting

    g = Greeter()
    g.hello('sup')
    g.hello('hi')
    nt.assert_equal(g.count, 2)

    # make sure it errors on non methods
    @method_dec
    def hello(greeting):
        return greeting

    with nt.assert_raises(RequiredSelfError):
        hello(10)

def test_hook_static():
    """
    @static marks function as not having self param
    """
    def counter(self, *args):
        self.count += 1
        yield

    EVENTS = []
    @static
    def log_greeting(greeting):
        EVENTS.append(greeting)
        yield

    method_dec = MultiDecorator()
    method_dec.add_hook(counter)
    method_dec.add_hook(log_greeting)

    class Greeter:
        def __init__(self):
            self.count = 0

        @method_dec
        def hello(self, greeting='hello'):
            return greeting

    g = Greeter()
    g.hello('sup')
    nt.assert_equal(g.count, 1)

    g2 = Greeter()
    g2.hello('sup2')
    g2.hello('sup3')
    nt.assert_equal(g2.count, 2)
    nt.assert_list_equal(EVENTS, ['sup', 'sup2', 'sup3'])

    # test that static works for non-method types
    EVENTS.clear()
    only_static_dec = MultiDecorator()
    only_static_dec.add_hook(log_greeting)
    @only_static_dec
    def hello(greeting):
        return greeting

    hello(1)
    hello(2)
    nt.assert_list_equal(EVENTS, [1,2])


def test_requires_self():
    @require_self
    def counter(self, *args):
        self.count += 1
        yield

    EVENTS = []
    @static
    def log_greeting(greeting):
        EVENTS.append(greeting)
        yield

    method_dec = MultiDecorator()
    method_dec.add_hook(counter)
    method_dec.add_hook(log_greeting)

    @method_dec
    def hello(greeting):
        return greeting

    with nt.assert_raises(RequiredSelfError):
        hello(10)
