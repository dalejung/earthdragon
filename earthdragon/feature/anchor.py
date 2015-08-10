"""
An anchor's behavior is a cascading list of Attrs where the hooks/pipelines/etc
are carried from each class to its subclasses.
"""
from collections import defaultdict, OrderedDict
from types import FunctionType

from ..pattern_match import pattern
from .attr import Attr
from ..meta import MetaMeta

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

@pattern
def _to_anchor(parent, child, bases):
    """
    if the parent_anchor is an Attr, we propogate it.
    if the child is not also an Attr, then we assume something went wrong
    the child class should know that it needs to be an Attr.
    """
    meta [match : parent, child]

    ~ Attr, Attr | parent, child
    ~ Attr, None | parent, Attr()
    ~ Attr, FunctionType | parent, Attr(child)
    ~ None, Attr | Attr(), child
    ~ None, None [when: bases == ()] | Attr(), Attr()
    ~ None, FunctionType | Attr(), Attr(child)

def propogate_anchor(dct, bases, name, preprocess=None):
    """
    When we find that the parent class defined the name as
    an anchor, we propogate the hooks from that method to the
    child class.

    Each subclass requires it's own copy since a hook might be added to a
    subclass anchor.
    """
    parent_anchor, child_anchor = parent_child_anchors(dct, bases, name)
    if preprocess:
        preprocess(parent_anchor, child_anchor)
    new_anchor = Attr.combine(parent_anchor, child_anchor)
    return new_anchor

def _parent_child(dct, bases, name):
    parent = _parent_anchor(bases, name)
    child = dct.get(name)
    return parent, child

def parent_child_anchors(dct, bases, name):
    """
    Returns a pair of attrs ready for combining.
    """
    parent, child = _parent_child(dct, bases, name)
    parent_anchor, child_anchor = _to_anchor(parent, child, bases)
    return parent_anchor, child_anchor

def _parent_anchor(bases, hook_name):
    for base in bases:
        return base.__dict__[hook_name]

class AnchorFuncError(Exception):
    pass

def _get_anchor_name(k, v):
    anchor_name = k
    if isinstance(v, AnchorFunc):
        anchor_name = v.name
    return anchor_name

def _check_funcs(funcs):
    if len(funcs) == 1:
        return True

    # Attr can be first entry. Cannot occur after a AnchorFunc.
    is_attr = lambda obj: isinstance(obj, Attr)
    if any(map(is_attr, funcs[1:])):
        raise AnchorFuncError("Cannot have a Attr after AnchorFuncs")

def _merge_anchor_funcs(funcs):
    """
    Merge a list of AnchorFuncs into an Attr. If the first element is
    an Attr, then we merge into that Attr.
    """
    _check_funcs(funcs)
    if isinstance(funcs, Attr):
        return funcs

    attr = Attr()
    if isinstance(funcs[0], Attr):
        attr = funcs[0]
        funcs = funcs[1:]

    for func in funcs:
        add_to_attr(attr, func)
    return attr

def aggregate_anchor_funcs(dct):
    """ aggregate a class dict into single Attrs per name """
    dct = filter(lambda x: isinstance(x[1], (Attr, AnchorFunc)), dct.items())
    items = [(_get_anchor_name(k, v), v) for k, v in dct]
    res = defaultdict(list)
    for k, v in items:
        res[k].append(v)

    update = {k:_merge_anchor_funcs(funcs) for k, funcs in res.items()}
    return update

def aggregate_parent_anchors(dct, bases):
    """
    If the super class has an Attr, we're assuming it is an Anchor.
    """
    base_dict = bases[0].__dict__
    update = OrderedDict()
    for k, v in base_dict.items():
        if isinstance(v, Attr):
            if k in update:
                raise AnchorDuplicateAttr(k)
            update[k] = propogate_anchor(dct, bases, k)
            continue
    return update

def anchor_updates(dct, bases):
    """
    Bases on the superclasses, generate a dict of new Attrs to
    update the child dct. Basically creates a manifest of all
    current anchors affecting the class.

    For now we assume that anchors have been propogates properly to the
    super classes, so this doesn't go up the mro to find anchors originally
    defined in a grandparent class.
    """
    dct = dct.copy()
    anchor_funcs = aggregate_anchor_funcs(dct)
    dct.update(anchor_funcs)

    propogated_anchors = aggregate_parent_anchors(dct, bases)
    anchor_funcs.update(propogated_anchors)
    return anchor_funcs

class AnchorMeta(MetaMeta):
    def __new__(cls, name, bases, dct):
        if bases:
            update = anchor_updates(dct, bases)
            dct.update(update)
        return super().__new__(cls, name, bases, dct)
