from ..class_util import class_attrs

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
