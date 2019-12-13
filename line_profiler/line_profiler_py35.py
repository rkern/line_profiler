""" This file is only imported in python 3.5 environments """
import functools

def wrap_coroutine(self, func):
    """
    Wrap a Python 3.5 coroutine to profile it.
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwds):
        self.enable_by_count()
        try:
            result = await func(*args, **kwds)
        finally:
            self.disable_by_count()
        return result
    return wrapper
