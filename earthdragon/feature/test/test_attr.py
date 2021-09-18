import pytest

from ..attr import Attr


def test_combine_func():
    a = Attr(lambda x: x+1)
    b = Attr(lambda x: x+2)
    c = Attr.combine(a, b)

    # func should have proogated
    assert c.decorator.orig_func is True
    assert c.decorator(1) == 3

    # switch order
    d = Attr.combine(b, a)
    assert d.decorator(1) == 2

    # add attr without func
    f = Attr.combine(b, a, Attr())
    assert f.decorator(1) == 2


def test_combine_pipeline():
    a = Attr(lambda x: x+1)
    a.add_pipeline(lambda x: x**x)
    b = Attr(lambda x: x+2)
    b.add_pipeline(lambda x: x-10)

    c = Attr.combine(a, b)

    # should be equivalent of ((x + 2) ** (x + 2) - 10)
    def correct(x):
        return ((x + 2) ** (x + 2) - 10)

    assert c.decorator(10) == correct(10)


def test_combine_empty_attr():
    a = Attr()
    b = Attr()
    c = Attr.combine(a, b)
    assert c.decorator.orig_func is None


def test_find_orig_func():
    class GrandFather:
        def a(self):
            return 1

    class Parent(GrandFather):
        a = Attr()
        a.add_pipeline(lambda x: x+2)

    class Child(Parent):
        a = Attr()
        a.add_pipeline(lambda x: x+1)

    p = Parent()
    assert p.a() == 3

    # note that the pipeline does not cascade
    # Attr only finds the original func.
    # the propogate is done via metaclass
    # this behavior could change...
    c = Child()
    assert c.a() == 2
