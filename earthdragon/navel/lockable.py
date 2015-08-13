from earthdragon.typelet import Int
from earthdragon.multidecorator import (
    MultiDecorator,
    require_self,
    only_self,
    first
)
from ..feature import Attr, features

class UnexpectedMutationError(Exception):
    pass

class Lockable:

    _in_flight = Int(default=0)

    @first
    @only_self
    def unlock(self):
        self._in_flight += 1
        yield
        self._in_flight -= 1

    __init__ = Attr()
    __init__.add_hook(unlock)


    @first
    @require_self
    def _lock_check(self, name, value): # replicate setattr signature
        if name in ['_in_flight']:
            return

        if self._in_flight <= 0:
            raise UnexpectedMutationError(name)
        yield

    __setattr__ = Attr()
    __setattr__.add_hook(_lock_check)

mutate = MultiDecorator()
mutate.add_hook(Lockable.unlock)
