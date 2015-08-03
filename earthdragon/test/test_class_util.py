from ..class_util import get_unbounded_super
import nose.tools as nt

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
    meth = get_unbounded_super(c, attr)
    nt.assert_is(meth, object.__init__)

    class Parent:
        def __init__(self):
            pass

    class Child(Parent):
        def __init__(self):
            pass

    c = Child()
    attr = c.__init__
    meth = get_unbounded_super(c, attr)
    nt.assert_is(meth, Parent.__init__)

    meth = get_unbounded_super(c, '__init__')
    nt.assert_is(meth, Parent.__init__)

class Parent:
    def __init__(self, bob):
        super().__init__()

    def hi(self):
        print('parent hi')

class Surrogate:
    def hello(self, greeting):
        print(greeting)
        # super causes hello() to gain a closure
        super()

class Child(Parent):
    def hi(self):
        print('child hi')
        super().hi()

setattr(Parent, 'hello', Surrogate.hello)

p = Parent(1)
c = Child(2)
