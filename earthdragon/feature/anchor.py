"""
An anchor's behavior is a cascading list of Attrs where the hooks/pipelines/etc
are carried from each class to its subclasses.

Implicit in discussing anchors is class hierarchy. We use the terms parent/child
where child is always the current context. Which means that we don't touch the
child when processing the parent. We always process the class dicts root down.
"""
from collections import defaultdict, OrderedDict
from types import FunctionType

from ..pattern_match import pattern
from .attr import Attr
from ..meta import MetaMeta

class AnchorFuncError(Exception):
    pass

class InvalidAnchorOverrideError(Exception):
    pass

class AnchorFunc:
    """
    Mark certain functions as being wrapped functions for an Attr.

    Instead of:
    ```
    def some_hook(self):
        yield
    __init__ = Attr()
    __init__.add_hook(some_hook)
    ```
    we can do:
    ```
    @hook('__init__')
    def some_hook(self):
        yield

    """
    def __init__(self, name):
        self.name = name

    def __call__(self, func):
        self.func = func
        return self

class hook(AnchorFunc): pass

class pipeline(AnchorFunc): pass

class transform(AnchorFunc): pass

def add_to_attr(attr, func):
    """ utility func to add AnchorFunc to an Attr """
    assert isinstance(func, AnchorFunc)
    anchor_func_type = func.__class__.__name__
    adder = getattr(attr, 'add_{type}'.format(type=anchor_func_type))
    adder(func.func)
    return attr

def _parent_anchors(bases):
    if not bases:
        return {}
    base_dict = bases[0].__dict__
    return {k:v for k, v in base_dict.items() if isinstance(v, Attr)}

def _get_anchor_name(k, v):
    anchor_name = k
    if isinstance(v, AnchorFunc):
        anchor_name = v.name
    return anchor_name

def _validate_funcs(funcs):
    if len(funcs) == 1:
        return True

    # Attr can be first entry. Cannot occur after a AnchorFunc.
    is_attr = lambda obj: isinstance(obj, Attr)
    if any(map(is_attr, funcs[1:])):
        raise AnchorFuncError("Cannot have a Attr after AnchorFuncs")

def _reduce_anchor_funcs(funcs):
    """
    Merge a list of AnchorFuncs into an Attr. If the first element is
    an Attr, then we merge into that Attr.
    """
    _validate_funcs(funcs)
    if isinstance(funcs, Attr):
        return funcs

    attr = Attr()
    if isinstance(funcs[0], Attr):
        attr = funcs[0]
        funcs = funcs[1:]

    for func in funcs:
        add_to_attr(attr, func)
    return attr

def _aggregate_anchor_funcs(dct):
    """ aggregate a class dict into single Attrs per name """
    dct = filter(lambda x: isinstance(x[1], (Attr, AnchorFunc)), dct.items())
    items = [(_get_anchor_name(k, v), v) for k, v in dct]
    res = defaultdict(list)
    for k, v in items:
        res[k].append(v)

    update = {k:_reduce_anchor_funcs(funcs) for k, funcs in res.items()}
    return update

def _merge_parent_child_anchors(dct, bases):
    """
    If the super class has an Attr, we're assuming it is an Anchor.
    """
    update = OrderedDict()
    for k, v in parent_anchors.items():
        update[k] = propogate_anchor(dct, bases, k)
        continue
    return update

_missing = object()

@pattern
def _to_anchor(parent, child):
    """
    if the parent_anchor is an Attr, we propogate it.
    if the child is not also an Attr, then we assume something went wrong
    the child class should know that it needs to be an Attr.
    """
    meta [match : parent, child]

    ~ Attr, Attr | parent, child
    ~ Attr, _missing | parent, Attr()
    ~ Attr, FunctionType | parent, Attr(child)
    ~ _missing, Attr | Attr(), child # new anchor

def anchor_updates(dct, bases):
    """
    Bases on the superclasses, generate a dict of new Attrs to
    update the child dct. Basically creates a manifest of all
    current anchors affecting the class.

    For now we assume that anchors have been propogates properly to the
    super classes, so this doesn't go up the mro to find anchors originally
    defined in a grandparent class.
    """
    parent_anchors = _parent_anchors(bases)
    child_anchors = _aggregate_anchor_funcs(dct)

    all_anchors = set(child_anchors) | set(parent_anchors)

    update = {}
    for name in all_anchors:
        parent = parent_anchors.get(name, _missing)
        child = child_anchors.get(name, _missing)

        if child is _missing:
            child = dct.get(name, _missing)
        parent, child = _to_anchor(parent, child)

        new_anchor = Attr.combine(parent, child)
        update[name] = new_anchor
    return update

class AnchorMeta(MetaMeta):
    def __new__(cls, name, bases, dct):
        update = anchor_updates(dct, bases)
        dct.update(update)
        return super().__new__(cls, name, bases, dct)
