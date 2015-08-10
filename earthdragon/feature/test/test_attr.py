import nose.tools as nt

from ..attr import Attr

def test_combine_func():
    a = Attr(lambda x: x+1)
    b = Attr(lambda x: x+2)
    c = Attr.combine(a, b)

    # func should have proogated
    nt.assert_true(c.decorator.orig_func)
    nt.assert_equal(c.decorator(1), 3)

    # switch order
    d = Attr.combine(b, a)
    nt.assert_equal(d.decorator(1), 2)

    # add attr without func
    f = Attr.combine(b, a, Attr())
    nt.assert_equal(f.decorator(1), 2)

def test_combine_pipeline():
    a = Attr(lambda x: x+1)
    a.add_pipeline(lambda x: x**x)
    b = Attr(lambda x: x+2)
    b.add_pipeline(lambda x: x-10)

    c = Attr.combine(a, b)

    # should be equivalent of ((x + 2) ** (x + 2) - 10)
    correct = lambda x: ((x + 2) ** (x + 2) - 10)
    nt.assert_equal(c.decorator(10), correct(10))

def test_combine_empty_attr():
    a = Attr()
    b = Attr()
    c = Attr.combine(a, b)
    nt.assert_is_none(c.decorator.orig_func)

class GrandFather:
    def a(self):
        return 1

class Parent(GrandFather):
    a = Attr()

class Child(Parent):
    a = Attr()

c = Child()
c.a()
