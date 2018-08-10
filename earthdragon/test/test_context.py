import unittest

from nose.tools import (
    assert_count_equal,
    assert_is,
    assert_is_not,
    assert_not_in,
    assert_equal
)

from ..context import WithScope


class WithScopeTest(unittest.TestCase):
    def setUp(self):
        pass

    def test_context_util(self):
        bob = object()
        orig_bob = bob
        new_bob = object()
        out = {}
        with WithScope(out):
            dale = 123
            bob = new_bob

        # while original bob is restored,
        # we still have access to the with scope bob
        assert_count_equal(out['new_only'], ['dale'])
        assert_count_equal(out['new_vars'], ['dale', 'bob'])
        assert_count_equal(out['modified_vars'], ['bob'])
        assert_is(out['new_vars']['bob'], new_bob)
        assert_is_not(out['new_vars']['bob'], bob)

        # dale should be removed
        assert_not_in('dale', locals())
        assert_is(bob, orig_bob)

    def test_exit_handler(self):
        out = {}

        def handler(self, _out):
            assert_is(out, _out)
            assert_is(self.out, _out)
            assert_equal(_out['new_vars']['hallo'], 123)

        with WithScope(out, exit_handler=handler):
            hallo = 123
