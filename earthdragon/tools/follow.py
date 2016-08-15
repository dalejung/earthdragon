try:
    import pandas
    from ._follow import *
except ImportError as e:
    Follow = None
    msg = str(e)
    if msg != "No module named 'pandas'":
        raise
