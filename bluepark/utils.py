from functools import wraps
from typing import Callable, Any, Awaitable


def cached_async_method(func: Callable[[Any, str, int], Awaitable]):
    '''A decorator that caches the return value of an async callable with its name and prefix.'''
    name = '_cached_' + func.__name__

    @wraps(func)
    async def wrapper(instance, *args, **kwargs):
        # If the value is not cached, first call the wrapped function
        if name not in instance.__dict__:
            instance.__dict__[name] = await func(instance, *args, **kwargs)
        return instance.__dict__[name]
    return wrapper


class cached_property:
    '''A decorator that caches the return value of a callable with its name'''
    def __init__(self, func):
        self.func = func
        self.__doc__ = getattr(func, '__doc__')
        self.name = func.__name__

    def __get__(self, instance, cls=None):
        if instance is None:
            return self

        if self.name not in instance.__dict__:
            instance.__dict__[self.name] = self.func(instance)
        return instance.__dict__[self.name]
