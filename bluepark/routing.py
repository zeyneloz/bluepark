from typing import Callable


class BaseRouter:
    DEFAULT_HTTP_METHODS = ('GET', 'HEAD', 'OPTIONS')

    def __init__(self, prefix: str='', default_http_methods: list=None) -> None:
        self.prefix = prefix
        if default_http_methods is not None:
            self.DEFAULT_HTTP_METHODS = (method.upper() for method in default_http_methods)

    def register(self, rule: str, view_function: Callable, rule_name: str=None, **kwargs) -> None:
        raise NotImplementedError()


class Router(BaseRouter):

    def register(self, rule: str, view_function: Callable, rule_name: str=None, **kwargs) -> None:
        '''
        Add a new url rule to the rule list.

        :param rule:
        :param view_function:
        :param rule_name:
        :param kwargs:
        '''

        if rule_name is None:
            rule_name = view_function.__name__

        # If there is no `method` kwarg provided, use default methods
        methods = kwargs.get('methods', self.DEFAULT_HTTP_METHODS)
        methods = [method.upper() for method in methods]

        # TODO handle rule overriding
