from earthdragon.typelet import Bool
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

    _locked = Bool()

    @first
    @only_self
    def unlock(self):
        self._locked = False
        yield
        self._locked = True

    __init__ = Attr()
    __init__.add_hook(unlock)


    @first
    @require_self
    def _lock_check(self, name, value): # replicate setattr signature
        if name in ['_locked']:
            return

        if self._locked:
            raise UnexpectedMutationError(name)
        yield

    __setattr__ = Attr()
    __setattr__.add_hook(_lock_check)

mutate = MultiDecorator()
mutate.add_hook(Lockable.unlock)
