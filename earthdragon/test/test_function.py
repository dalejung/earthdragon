from ..function import MultiDecorator, DuplicateWrapperError

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
        print(context)
        EVENTS.append(ret)


    func_dec = MultiDecorator()
    func_dec.add_hook(log_return)

    @func_dec
    def hello(val):
        return val + 1

    hello(100)
    nt.assert_equal(EVENTS[0], 101)
