import pytest

from ..cache import staticcache


@staticcache
def fake_func(dale=1):
    import datetime
    return datetime.datetime.now()


@pytest.mark.xfail(reason='default vars need to be handled')
def test_bare_decorator():
    first = fake_func()
    second = fake_func()
    assert first == second

    third = fake_func(3)
    assert first != third

    fourth = fake_func(1)
    assert first == fourth
