import pytest # noqa

from ..func_util import (
    get_invoked_args
)

from . import util
util.preamble()


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
