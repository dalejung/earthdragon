from ..class_util import (
    get_unbounded_super,
    set_class_attr,
    class_attrs,
)

from nose.tools import (
    assert_is,
    assert_raises,
)


def test_get_unbounded_super():
    class GrandParent:
        pass

    class Parent(GrandParent):
        init_count = 0

        def __init__(self):
            self.init_count += 1
            super().__init__()

    class Interloper(Parent):
        pass

    class Child(Interloper):
        __init__ = Parent.__init__

    c = Child()
    attr = c.__init__
    owner, meth = get_unbounded_super(c, attr)
    assert_is(meth, object.__init__)

    class Parent:
        def __init__(self):
            pass

    class Child(Parent):
        def __init__(self):
            pass

    c = Child()
    attr = c.__init__
    owner, meth = get_unbounded_super(c, attr)
    assert_is(meth, Parent.__init__)

    owner, meth = get_unbounded_super(c, '__init__')
    assert_is(meth, Parent.__init__)


def test_set_class_attr():
    class Parent:
        pass

    class Surrogate:
        def hello(self, greeting):
            print(greeting)
            # super causes hello() to gain a closure
            super()

    p = Parent()

    setattr(Parent, 'hello', Surrogate.hello)

    with assert_raises(TypeError):
        p.hello('hi')

    set_class_attr(Parent, 'hello', Surrogate.hello)
    p.hello('hi')


def test_unbounded_super():
    class GrandParent:
        def hi(self):
            print('grandparent hi')

    class Parent(GrandParent):
        def __init__(self, bob):
            super().__init__()

        def hi(self):
            print('parent hi')

    class Child(Parent):
        def hi(self):
            print('child hi')
            super().hi()

    c = Child(1)
    owner, meth = get_unbounded_super(c, 'hi')
    assert_is(owner, Parent)
    assert_is(meth, Parent.hi)

    owner, meth = get_unbounded_super(Child, 'hi')
    assert_is(owner, Parent)
    assert_is(meth, Parent.hi)
    owner, meth = get_unbounded_super(Parent, 'hi')
    assert_is(owner, GrandParent)
    assert_is(meth, GrandParent.hi)

    owner, meth = get_unbounded_super(GrandParent, 'hi')
    assert_is(owner, object)
    assert_is(meth, None)

    owner, meth = get_unbounded_super(GrandParent, '__init__')
    assert_is(owner, object)
    assert_is(meth, object.__init__)


def test_class_attrs():
    class Bob:
        dale = 1

    class Frank(Bob):
        whee = 2

    attrs = class_attrs(Frank)
