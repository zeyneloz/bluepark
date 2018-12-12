from typing import Optional, Callable

from .utils.types import RequestMethods, HTTPView


class URLRule:

    def __init__(self, view_function: HTTPView, rule_name: str, methods: RequestMethods):
        self.view_function = view_function
        self.rule_name = rule_name
        self.methods = methods

    def is_method_allowed(self, method: str):
        '''Return whether the `method` is in `self.methods` or not.'''
        return method in self.methods


class BaseRouter:
    # Default HTTP methods to be used
    _default_http_methods = ('GET', 'HEAD', 'OPTIONS')

    def __init__(self, default_http_methods: RequestMethods = None, prefix: str = '') -> None:
        # Holds all of the url rules for this router
        self._rules = {}

        # Prefix to be added the beginning of every url registered using this router
        self.prefix = self.normalize_path(prefix)
        if default_http_methods is not None:
            self._default_http_methods = (method.upper() for method in default_http_methods)

    def normalize_path(self, path: str):
        '''
        Given a path string, remove leading slash and put a trailing slash.

        :param path: The URL path as string
        '''
        if path == '':
            return ''
        return path.strip('/') + '/'

    def add_rule(self, path: str, view_function: HTTPView,
                 rule_name: str = None, methods: RequestMethods = None) -> None:
        '''
        Add a new url rule to the rules.

        :param path:
        :param view_function:
        :param rule_name:
        :param methods:
        '''

        if rule_name is None:
            rule_name = view_function.__name__

        # If there is no `method` kwarg provided, use default methods
        if methods is None:
            methods = self._default_http_methods
        else:
            methods = [method.upper() for method in methods]

        normalized_path = self.normalize_path(path)
        prefixed_path = '/' + self.prefix + normalized_path
        rule = URLRule(view_function, rule_name, methods)
        self._add_rule(prefixed_path, rule)

    def _add_rule(self, path: str, rule: URLRule):
        self._rules[path] = rule

    def route(self, path: str, rule_name: str = None, methods: RequestMethods = None) -> Callable:
        '''A decorator for add_rule.'''
        def wrapper(view_function: HTTPView):
            self.add_rule(path, view_function, rule_name, methods)
            return view_function
        return wrapper


class MainRouter(BaseRouter):
    '''
    Singleton main router. Every URL rule ends up here.
    '''

    def get_rule_for_path(self, path: str) -> Optional[URLRule]:
        return self._rules.get(path, None)


class Router(BaseRouter):

    _main_router: MainRouter = None

    def _add_to_main_router(self, normalized_path: str, rule: URLRule):
        '''Whenever there is a new URL added, add it to main router as well.'''
        if self._main_router is None:
            return
        self._main_router._add_rule(normalized_path, rule)

    def _set_main_router(self, main_router: MainRouter):
        '''
        A Router can be initialized without a main router. Use this method to set it later.

        All of the existing rules will be added to main router.
        '''
        self._main_router = main_router

        for path, rule in self._rules.items():
            self._add_to_main_router(path, rule)

    def _add_rule(self, path: str, rule: URLRule):
        super(Router, self)._add_rule(path, rule)
        self._add_to_main_router(path, rule)
