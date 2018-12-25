import operator

empty_object = object()


def simple_proxy_method_proxy(func):
    def inner(self, *args):
        if self._wrapped == empty_object:
            raise RuntimeError('Proxy object is empty')
        return func(self._wrapped, *args)

    return inner


class SimpleProxy:
    '''A Proxy objects that acts as a place holder for an object
    so that the instantiation if the wrapped object can be delayed.'''

    _wrapped = None

    def __init__(self):
        self._wrapped = empty_object

    def _wrap(self, obj):
        self._wrapped = obj

    __getattr__ = simple_proxy_method_proxy(getattr)
    __delattr__ = simple_proxy_method_proxy(delattr)

    def __setattr__(self, name, value):
        if name == '_wrapped':
            self.__dict__["_wrapped"] = value
        else:
            setattr(self._wrapped, name, value)

    __str__ = simple_proxy_method_proxy(str)
    __bool__ = simple_proxy_method_proxy(bool)
    __bytes__ = simple_proxy_method_proxy(bytes)

    __dir__ = simple_proxy_method_proxy(dir)

    __class__ = property(simple_proxy_method_proxy(operator.attrgetter("__class__")))
    __eq__ = simple_proxy_method_proxy(operator.eq)
    __lt__ = simple_proxy_method_proxy(operator.lt)
    __gt__ = simple_proxy_method_proxy(operator.gt)
    __ne__ = simple_proxy_method_proxy(operator.ne)
    __hash__ = simple_proxy_method_proxy(hash)

    __getitem__ = simple_proxy_method_proxy(operator.getitem)
    __setitem__ = simple_proxy_method_proxy(operator.setitem)
    __delitem__ = simple_proxy_method_proxy(operator.delitem)
    __iter__ = simple_proxy_method_proxy(iter)
    __len__ = simple_proxy_method_proxy(len)
    __contains__ = simple_proxy_method_proxy(operator.contains)


current_app = SimpleProxy()
