import unittest
from collections import Counter

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
        assert Counter(list(out['new_only'])) == Counter(['dale'])

        assert Counter(list(out['new_vars'])) == Counter(['dale', 'bob'])
        assert Counter(list(out['modified_vars'])) == Counter(['bob'])
        assert out['new_vars']['bob'] is new_bob
        assert out['new_vars']['bob'] is not bob

        # dale should be removed
        # 3.12 seems to have changed behavior to where it sets it as None?
        # RuntimeWarning: assigning None to unbound local 'dale'
        #   ctypes.pythonapi.PyFrame_LocalsToFast(

        assert locals()['dale'] is None
        assert bob is orig_bob

    def test_exit_handler(self):
        out = {}

        def handler(self, _out):
            assert out is _out
            assert self.out is _out
            assert _out['new_vars']['hallo'] == 123

        with WithScope(out, exit_handler=handler):
            hallo = 123  # noqa: F841
