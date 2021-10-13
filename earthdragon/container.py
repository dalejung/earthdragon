from collections.abc import MutableMapping
from collections import UserDict

from frozendict import frozendict


class SetOnceDict(UserDict):
    """
    dict where a key can only be set once.
    """
    def __setitem__(self, key, value):
        if key in self:
            raise KeyError(f"{key} has already been set")
        super().__setitem__(key, value)

    def __hash__(self):
        items = []
        for k, v in self.items():
            if isinstance(v, MutableMapping):
                v = frozenset(v.items())
            items.append((k, v))
        return hash(frozenset(items))
