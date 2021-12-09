import logging
import inspect

from .func_util import resolve_module


def get_logger_name(depth=2):
    frm = inspect.stack()[depth]
    mod = inspect.getmodule(frm[0])

    name = __name__
    if mod is not None:
        name = mod.__name__

    if name == '__main__':
        import __main__
        name = __main__.__spec__.name

    return name


def clogger(name=None):
    if name is None:
        name = get_logger_name()
    logger = logging.getLogger(name)

    try:
        from systemd.journal import JournalHandler
        logger.addHandler(JournalHandler())
    except ImportError:
        pass

    return logger

