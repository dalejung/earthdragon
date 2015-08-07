from ..pattern_match import pattern
from types import FunctionType
from .attr import Attr

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

def parent_child_anchors(dct, bases, name):
    """
    Returns a pair of attrs ready for combining.
    """
    parent = _parent_anchor(bases, name)
    child = dct.get(name)
    parent_anchor, child_anchor = _to_anchor(parent, child, bases)
    return parent_anchor, child_anchor

def _parent_anchor(bases, hook_name):
    for base in bases:
        return base.__dict__[hook_name]
