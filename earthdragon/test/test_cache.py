import asyncio
import time

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


def test_decorator_async():
    sleep_time = .1
    loop = asyncio.new_event_loop()

    @staticcache
    async def asyncfunc(dale=1):
        await asyncio.sleep(sleep_time)
        return time.monotonic()

    try:
        asyncio.set_event_loop(loop)

        # make sure this takes a second
        before = time.monotonic()
        res1 = loop.run_until_complete(asyncfunc(3))
        after = time.monotonic()
        assert after - before >= sleep_time

        # this one should cache
        before = time.monotonic()
        res2 = loop.run_until_complete(asyncfunc(3))
        after = time.monotonic()
        # check that we use cache and don't sleep
        assert after - before < .01

        assert res1 == res2

        # use new arg. cache is cold
        before = time.monotonic()
        res3 = loop.run_until_complete(asyncfunc(2))
        after = time.monotonic()
        # we should be sleeping again since new arg
        assert after - before >= sleep_time
        assert res3 != res1

    finally:
        loop.close()
