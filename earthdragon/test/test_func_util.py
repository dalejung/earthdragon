import pytest # noqa

from ..func_util import (
    get_invoked_args,
    get_func_ns,
    make_cell,
    get_argspec,
    SetOnceDict,
    get_class_from_unbound,
    convert_argspec_to_dict,
)


# here to test get_func_ns
def fake_func():
    pass


def test_func_ns():
    def nested_func():
        pass
    func_ns = get_func_ns(fake_func)
    assert func_ns.startswith('earthdragon.test.test_func_util')

    # honestly not sure what this should be. Just putting this here to specify
    # current behavior
    nested_func_ns = get_func_ns(nested_func)
    assert nested_func_ns == 'earthdragon.test.test_func_util.nested_func'

    func_ns = get_func_ns(make_cell)
    assert func_ns == 'earthdragon.func_util.make_cell'

    class CallableClass:
        def __init__(self, ret):
            self.ret = ret

        def __call__(self):
            return self.ret

    cc = CallableClass(1)
    ns = get_func_ns(cc)
    assert ns == 'earthdragon.test.test_func_util.CallableClass'


def test_get_invoked_args_nodefaults():
    def invoker(a, b):
        return a, b

    invoked_args = get_invoked_args(invoker, 1, 2)
    correct_vals = {'b': 2, 'a': 1}
    assert invoked_args == correct_vals


def test_get_invoked_args_defaults():
    def invoker(a, b, c=3):
        return a, b, c

    invoked_args = get_invoked_args(invoker, 1, 2)
    correct_vals = {'a': 1, 'b': 2, 'c': 3}
    assert invoked_args == correct_vals

    def invoker2(a, b, *args, c=3):
        return a, b, c

    invoked_args = get_invoked_args(invoker, 1, 2)
    correct_vals = {'a': 1, 'b': 2, 'c': 3}
    assert invoked_args == correct_vals


def test_get_invoked_args_kw_only():
    def invoker(a, b, *args, c=3, **kwargs):
        return a, b, c

    invoked_args = get_invoked_args(invoker, 1, 2, 3, c=4, d=5)
    correct_vals = {
        'a': 1, 'b': 2, 'c': 4, 'args': (3,), 'kwargs': {'d': 5}
    }
    assert invoked_args == correct_vals


def test_get_invoked_args_too_many_args():
    def invoker(a, b, c=3):
        return a, b, c

    with pytest.raises(TypeError):
        get_invoked_args(invoker, 1, 2, 3, 4, d=5)


def test_get_invoked_args_unexpected_kw():
    def invoker(a, b, c=3):
        return a, b, c

    with pytest.raises(TypeError):
        get_invoked_args(invoker, 1, 2, d=5)


def test_get_invoked_args_multiple_values():
    def invoker(a, b, c=3):
        return a, b, c

    with pytest.raises(TypeError):
        get_invoked_args(invoker, 1, 2, 3, c=5)


def test_pos_arg_with_kw():
    """
    This is to test when a pos arg is invokved via kw. This makes *args smaller
    than argspec.args which has to be handled.
    """
    def kwonly_test(a, b, *rollupargs, c=None):
        return locals()

    inv = get_invoked_args(kwonly_test, 1, b='b', c=3)
    assert inv == {'a': 1, 'b': 'b', 'c': 3, 'rollupargs': ()}


def test_full_platter():
    def full_platter(a, b, /, *rolledup, c=None, secret='shh',
                     **rolledupkwargs):
        return a, b

    inv = get_invoked_args(full_platter, 1, 2, 3, 4, c='c', bob=1, howdy=False)
    assert inv == {
        'a': 1,
        'b': 2,
        'rolledup': (3, 4),
        'c': 'c',
        'secret': 'shh',
        'rolledupkwargs': {
            'bob': 1,
            'howdy': False,
        }
    }


def test_arglist_order():
    def invoker(a, b, c=3):
        return a, b, c

    with pytest.raises(ValueError,
                       match="Not enough args passed in"):
        get_invoked_args(invoker, 1, c=5)


def test_defaulted_args():
    def defaulted_kw(hi=1):
        pass

    inv_args = get_invoked_args(defaulted_kw)
    assert inv_args == {'hi': 1}


def test_missing_args():
    def invoker(a, b, c=3):
        return a, b, c
    with pytest.raises(ValueError,
                       match="Not enough args passed in."):
        get_invoked_args(invoker, 1)


def test_func_with_defaults():
    def howdy(a, b='b', c='c', **kwargs):
        pass

    inv = get_invoked_args(howdy, 1, c=3, howdy='hi')
    assert inv == {'a': 1, 'c': 3, 'b': 'b', 'kwargs': {'howdy': 'hi'}}


def test_invovked_args_methods():
    class Bob:
        def sing(self, song):
            return song

    b = Bob()
    inv = get_invoked_args(b.sing, 'Final Countdown')
    assert inv['self'] is b
    assert inv['song'] == 'Final Countdown'

    argspec = get_argspec(b.sing)
    inv2 = get_invoked_args(argspec, b, 'Final Countdown')
    assert inv2['self'] is b
    assert inv2['song'] == 'Final Countdown'

    argdict = convert_argspec_to_dict(argspec)
    assert argdict == {'args': ['self', 'song']}


def test_fingerprint_unbounded_method():
    class ClassExample2:
        @classmethod
        def cls_method(cls, obj):
            return obj

        def regular_method(self, obj):
            return obj

    assert get_class_from_unbound(ClassExample2.regular_method) == 'ClassExample2'
    assert get_class_from_unbound(ClassExample2.cls_method) == 'ClassExample2'


if __name__ == '__main__':
    pass
