import re
import typing

from .exceptions import PathRegisterError
from .utils.converters import CONVERTERS
from .utils.types import RequestMethods, HTTPView

_PATH_PARAM_REGEX = re.compile(
    r'<(?:(?P<type>[^>:]+):)?(?P<name>\w+)>'
)


def _parse_path(path: str) -> typing.Tuple[typing.Pattern, dict]:
    '''Return path string as regex and converters'''
    path_regex = '^'
    converters = {}
    last_index = 0

    for match in _PATH_PARAM_REGEX.finditer(path):
        param_type = match.group('type')
        param_name = match.group('name')

        if param_type not in CONVERTERS:
            raise PathRegisterError(f'Invalid parameter type: {param_type}')

        if param_name in converters:
            raise PathRegisterError(f"You can't use the same parameter name more than once in a URL: {path}")

        converter = CONVERTERS[param_type]
        path_regex += f'{path[last_index:match.start()]}(?P<{param_name}>{converter.regex})'
        converters[param_name] = converter
        last_index = match.end()

    path_regex += f'{path[last_index:]}$'
    return re.compile(path_regex), converters


class URLRule:
    '''Represents a registered URL(path).'''

    def __init__(
            self,
            original_path: str,
            regex: typing.Pattern,
            converters: dict,
            view_function: HTTPView,
            rule_name: str,
            methods: RequestMethods
    ):
        self.original_path = original_path
        self.regex = regex
        self.converters = converters
        self.view_function = view_function
        self.rule_name = rule_name
        self.methods = methods

        self.parsed_params: dict = None

    def is_method_allowed(self, method: str):
        '''Return whether the `method` is in `self.methods` or not.'''
        return method in self.methods

    def match(self, path: str) -> bool:
        '''
        Return True if path matches the regex.
        Parse URL parameters and build a dict with their converted values for later use.
        '''
        match = self.regex.match(path)
        if match:
            params = match.groupdict()
            self.parsed_params = {name: self.converters[name].value(value) for name, value in params.items()}
            return True
        return False


class BaseRouter:
    # Default HTTP methods to be used
    _default_http_methods = ('GET', 'HEAD', 'OPTIONS')

    def __init__(self, default_http_methods: RequestMethods = None, prefix: str = '/') -> None:
        # Holds all of the url rules for this router
        self._rules: typing.MutableMapping[str, URLRule] = {}

        # Prefix to be added the beginning of every url registered using this router
        self.prefix = self.normalize_prefix(prefix)

        if default_http_methods is not None:
            self._default_http_methods = (method.upper() for method in default_http_methods)

    def normalize_prefix(self, prefix: str) -> str:
        '''Check if prefix has leading slash. Remove trailing slash.'''
        if not prefix.startswith('/'):
            raise PathRegisterError('Prefix must start with a slash')
        if prefix == '/':
            return prefix
        return prefix.rstrip('/')

    def normalize_path(self, path: str) -> str:
        '''
        Check if path has leading slash.

        :param path: The URL path as string
        '''
        if not path.startswith('/'):
            raise PathRegisterError('Path must start with a slash')
        return path

    def prefixed_path(self, path: str) -> str:
        '''Return given path with prefix.'''
        return f'{self.prefix.rstrip("/")}{path}'

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
        prefixed_path = self.prefixed_path(normalized_path)

        path_regex, path_converters = _parse_path(prefixed_path)
        rule = URLRule(
            original_path=prefixed_path,
            regex=path_regex,
            converters=path_converters,
            view_function=view_function,
            rule_name=rule_name,
            methods=methods
        )
        self._add_rule(rule_name, rule)

    def _add_rule(self, rule_name: str, rule: URLRule):
        # TODO, raise error if rule_name is already registered
        self._rules[rule_name] = rule

    def route(self, path: str, rule_name: str = None, methods: RequestMethods = None) -> typing.Callable:
        '''A decorator for add_rule.'''

        def wrapper(view_function: HTTPView):
            self.add_rule(path, view_function, rule_name, methods)
            return view_function

        return wrapper

    def on_error(self, status_code: int = None) -> None:
        pass


class MainRouter(BaseRouter):
    '''
    Singleton main router. Every URL rule ends up here.
    '''

    def get_rule_for_path(self, path: str) -> typing.Optional[URLRule]:
        '''
        Iterate over all registered rules and try to math the path with rule regex.
        Return the rule if it matches the path. Return None if no rule matches.
        '''
        for rule in self._rules.values():
            if rule.match(path):
                return rule
        return None


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
