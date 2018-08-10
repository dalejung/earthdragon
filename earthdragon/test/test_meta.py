import pytest

from ..meta import MetaMeta, mro


def middle_matcher(start, end):
    def _match(key):
        if not (key.startswith(start) and key.endswith(end)):
            return False
        middle = key[len(start):-len(end)]
        return middle
    return _match


set_to_match = middle_matcher("set_", "_to")


def test_scope_add():
    class DummyMeta(MetaMeta):
        def setitem_handler(key, value, scope):
            mid_name = set_to_match(key)
            if not mid_name:
                return
            scope[mid_name] = value

    # first case. bob is undefined
    with pytest.raises(NameError):
        class DummyClass(metaclass=DummyMeta):
            l = bob
            dale = 1

    # using DummyMeta and setitem_handler, bob gets added to ns. no error
    class DummyClass(metaclass=DummyMeta):
        set_bob_to = 'whee'
        l = bob
        dale = 1

    assert DummyClass.l == 'whee'
    # set_bob_to is not added to class. Just a directive
    assert hasattr(DummyClass, 'set_bob_to')


def test_scope_add_temporal():
    class DummyMeta2(MetaMeta):
        def setitem_handler(key, value, scope):
            mid_name = set_to_match(key)
            if not mid_name:
                return
            scope[mid_name] = value
            return False  # don't add directive to class

    # using DummyMeta and setitem_handler, bob gets added to ns. no error
    class DummyClass2(metaclass=DummyMeta2):
        set_bob_to = 'whee'
        l = bob
        dale = 1
    assert not hasattr(DummyClass2, 'set_bob_to')


class DummyMeta2(MetaMeta):
    def setitem_handler(key, value, scope):
        import inspect
        frames = inspect.stack()
        mid_name = set_to_match(key)
        if not mid_name:
            return
        scope[mid_name] = value
        return False  # don't add directive to class


# using DummyMeta and setitem_handler, bob gets added to ns. no error
class DummyClass2(metaclass=DummyMeta2):
    set_bob_to = 'whee'
    l = bob
    dale = 1


def test_mro():
    class MROMeta(type):
        def __new__(cls, name, bases, dct):
            dct['test_gen'] = mro(dct, bases, 'test')
            return super().__new__(cls, name, bases, dct)

    class GrandLeft:
        test = 'GrandLeft'

    class GrandRight(metaclass=MROMeta):
        test = 'GrandRight'

    class Child(GrandLeft, GrandRight, metaclass=MROMeta):
        test = 'Child'

    class GrandChild(Child):
        test = 'GC'

    class GrandChild2(Child):
        pass

    gc = GrandChild()

    assert gc.test == gc.test_gen

    gc2 = GrandChild2()
