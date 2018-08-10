from ..typecheck import (  # noqa: F401
    module_tree,
    TypeCheckProxy,
    typecheck_enable,
    typecheck_disable,
    is_typecheck_enabled,
    reset_manager
)


def bob(a, b: str):
    return a, b


def test_typecheck_enable_package():
    # enabling parent should enable children
    reset_manager()
    assert is_typecheck_enabled(None, full_module='fakepkg.fakemod') is False
    typecheck_enable('fakepkg')
    assert is_typecheck_enabled(None, full_module='fakepkg.fakemod') is True
    assert is_typecheck_enabled(None, full_module='fakepkg') is True


def test_typecheck_enable_module():
    # enabling children won't enable siblings
    reset_manager()
    typecheck_enable('fakepkg.fakemod1')
    assert is_typecheck_enabled(None, full_module='fakepkg.fakemod1') is True
    assert is_typecheck_enabled(None, full_module='fakepkg.fakemod2') is False
