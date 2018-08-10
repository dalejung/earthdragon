import pytest

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


@pytest.mark.xfail
def test_get_invoked_args_defaults():
    def invoker(a, b, c=3):
        return a, b, c

    invoked_args = get_invoked_args(invoker, 1, 2)
    correct_vals = {'a': 1, 'b': 2, 'c': 3}
    assert invoked_args == correct_vals
