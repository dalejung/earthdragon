import pytest # noqa

from ..cache import staticcache


@staticcache
def fake_func(dale=1, **kwargs):
    import datetime
    return datetime.datetime.now()


def test_decorator_bare():
    first = fake_func()
    second = fake_func()
    assert first == second

    third = fake_func(3)
    assert first != third

    fourth = fake_func(1)
    assert first == fourth


def test_decorator_kwargs():
    """
    Make sure kwargs works since it's a nested dict in the invoked args.
    Just make sure it's hashing.
    """
    first = fake_func(bob=1)
    second = fake_func(bob=1)
    assert first == second

    third = fake_func(3)
    assert first != third

    fourth = fake_func(bob=3)
    assert first != fourth
