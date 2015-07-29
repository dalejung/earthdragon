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
