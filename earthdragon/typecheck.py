import functools
import sys

_runtime_typecheck_module = False

try:
    import typeguard
    _runtime_typecheck_module = True
except ImportError:
    print('typeguard was not imported. earthdragon.typecheck not enabled')
    pass


class TypeCheckManager:
    def __init__(self):
        self.enabled_registry = {}
        self.proxies = []

    def toggle(self, module: str, flag: bool):
        old_val = self.enabled_registry.get(module, None)
        dirty = old_val != flag
        self.enabled_registry[module] = flag
        if dirty:
            self.recheck_proxies()

    def add_proxy(self, proxy):
        self.proxies.append(proxy)

    def recheck_proxies(self):
        for proxy in self.proxies:
            proxy.check_typecheck_enabled()

    def check_module_enabled(self, full_module: str):
        enabled, scope = self._check_module_enabled(full_module)
        return enabled

    def _check_module_enabled(self, full_module: str):
        # runtime module not installed. opt out
        if not _runtime_typecheck_module:
            return False, [full_module]

        # go up module tree looking for magic var

        tree = module_tree(full_module)

        scope = []
        for target_module in tree:
            scope.append(target_module)

            if target_module in self.enabled_registry:
                return self.enabled_registry[target_module], scope

        return False, scope

    def reset(self):
        self.enabled_registry = {}
        self.proxies = []


def module_tree(module: str):
    tree = []
    target_module = module
    while True:
        if not target_module: # reached top
            break
        tree.append(target_module)
        target_module, _, sub = target_module.rpartition('.')

    return tree

class TypeCheckProxy:
    def __init__(self, func, typecheck_checker=None, full_module=None):
        self.func = func

        if full_module is None:
            full_module = func.__module__
        self.full_module = full_module

        if typecheck_checker is None:
            typecheck_checker = is_typecheck_enabled
        self.typecheck_checker = typecheck_checker

        self.typecheck_enabled = False
        self._wrapped = None

    @property
    def wrapped(self):
        if self._wrapped is None:
            self._wrapped = typeguard.typechecked(self.func)
        return self._wrapped

    def check_typecheck_enabled(self):
        self.typecheck_enabled = self.typecheck_checker(self.func,
                                                        self.full_module)

    def __call__(self, *args, **kwargs):
        if not self.typecheck_enabled:
            return self.func(*args, **kwargs)

        return self.wrapped(*args, **kwargs)


# singleton api
_MANAGER = TypeCheckManager()


def typecheck_enable(module: str):
    """ enable typecheck for moduele """
    _MANAGER.toggle(module, True)


def typecheck_disable(module: str):
    _MANAGER.toggle(module, False)


def is_typecheck_enabled(func, full_module=None):
    if full_module is None:
        full_module = func.__module__
    return _MANAGER.check_module_enabled(full_module)


def typecheck(func):
    typecheck_proxy = TypeCheckProxy(func)
    _MANAGER.add_proxy(typecheck_proxy)
    return typecheck_proxy


def reset_manager():
    _MANAGER.reset()
    return _MANAGER
