Lower level constucts to build upon. In reality, the only restriction I am placing is that all code is valid python syntax.

## pattern matching

```python
@pattern
def multi_return(x):
    meta[match: x]

    ~ float [when: x > 1] | type(x), x, x
    ~ int [when: x > 100 and x < 150] | x, 'Between 100 and 150'
    ~ int [when: x > 10]| 'INT OVER 10'
    ~ int | type(x), x

nt.assert_equal(multi_return(1), (int, 1))
nt.assert_equal(multi_return(11), "INT OVER 10")
nt.assert_equal(multi_return(122), (122, "Between 100 and 150"))
nt.assert_equal(multi_return(1.1), (float, 1.1, 1.1))
with nt.assert_raises(UnhandledPatternError):
    nt.assert_equal(multi_return(0.1), (float, 1.1, 1.1))
```

## multidecorator

When wrapping a function, you often want to do one of 3 things:

1. Do a pre/post call.
2. Transform the function
3. Modify the output of the function

`Multidecorator` separates all 3 use cases. Building block for `Feature` which are like mixins but with specific logic concerning things like lifecycle events.


```python
@only_self
def counter(self):
    self.count += 1
    yield

EVENTS = []
@static
def log_greeting(greeting=None):
    ret, context = yield
    EVENTS.append((greeting, ret))

def goodbye(ret):
    return ret + '. goodbye'

count_and_log = MultiDecorator()
count_and_log.add_hook(counter)
count_and_log.add_hook(log_greeting)
count_and_log.add_pipeline(goodbye)

class Greeter:
    def __init__(self):
        self.count = 0

    @count_and_log
    def hello(self, greeting='hello'):
        return greeting

g = Greeter()
ret = g.hello()
nt.assert_equal(ret, 'hello. goodbye')

g.hello('howdy')
nt.assert_list_equal(EVENTS, [(None, 'hello. goodbye'), ('howdy', 'howdy. goodbye')])
nt.assert_equal(g.count, 2)
```
