try:
    import pandas
    from ._follow import *
except ImportError as e:
    msg = str(e)
    if msg != "No module named 'pandas'":
        raise
