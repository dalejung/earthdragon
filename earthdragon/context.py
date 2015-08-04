from contextlib import contextmanager
import inspect
from asttools import reload_locals

@contextmanager
def section(*args):
    """ just a dummy contextmanager. using it for doc """
    yield

class WithScope(object):
    """
    ContextManager that allows you to gather newly created variables
    while restoring the original executing scope.
    """
    def __init__(self, out={}, exit_handler=None):
        self.exit_handler = exit_handler
        self.out = out

    def __enter__(self):
        self.frame = inspect.stack()[1][0]
        self.original = self.scope.copy()
        return self.enter()

    def enter(self):
        # enter hook
        return self

    def reload_locals(self):
        reload_locals(self.frame)

    @property
    def scope(self):
        # for whatever reason. saving f_locals doesn't work in nose tests.
        # you have to re-access via frame to refresh
        return self.frame.f_locals

    def _gather_new_vars(self):
        new_scope = self.scope
        new_keys = set(new_scope.keys()) - set(self.original.keys())
        new_vars = {}
        for k in new_keys:
            new_v = new_scope[k]
            if new_v is self:
                continue
            new_vars[k] = new_v
        return new_vars

    def _gather_modified_vars(self):
        new_scope = self.scope
        # check for new items that shadowed existing items
        modified = {}
        for k, old_v in self.original.items():
            # deleted not treated same as modified
            if k not in new_scope:
                continue
            new_v = new_scope[k]
            if new_v is not old_v:
                modified[k] = new_v
        return modified

    def restore_scope(self):
        """
        Restores scope to original state. Note, new variables defined
        within `with` block will persist.
        """
        new_scope = self.scope
        for k, old_v in self.original.items():
            new_v = new_scope.setdefault(k, old_v) # will restore deletes
            # i think we'd be fine just resetting all items, but
            # only changing modified vars back
            if new_v is not old_v:
                new_scope[k] = old_v

        for k in self.out['new_only']:
            del new_scope[k]

        self.reload_locals()

    def __exit__(self, type, value, traceback):
        new_vars = self._gather_new_vars()
        modified = self._gather_modified_vars()
        new_only = new_vars.copy()
        new_vars.update(modified)

        # save new and modified vars.
        # TODO: could build list of deleted vars
        out = self.out
        out['new_only'] = new_only
        out['new_vars'] = new_vars
        out['modified_vars'] = modified

        self.restore_scope()

        if self.exit_handler:
            self.exit_handler(self, out)
