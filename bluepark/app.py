import typing

from .exceptions import HTTPException
from .globals import current_app
from .response import TextResponse
from .routing import MainRouter, Router
from .settings import Settings, DEFAULT_SETTINGS
from .utils.types import ASGIScope, ASGIAppInstance, HTTPMiddleware, ErrorHandler


# TODO type of request param
async def _http_exception_handler(request, e: HTTPException) -> TextResponse:
    '''Send 404 Not found HTTP message'''
    return TextResponse(e.message, status=e.status_code)


class BluePark:
    '''
    The BluePark class implements ASGI specifications.
    '''

    router: MainRouter = None

    def __init__(self) -> None:
        # TODO, settings from a file
        self.settings = Settings(DEFAULT_SETTINGS)

        # List of middleware functions for http connections.
        self._http_middleware = []

        # Initialize main router, every router is connected to the main router.
        self.router = MainRouter()

        # Error handlers
        self._error_handlers_by_code: typing.MutableMapping[int, ErrorHandler] = {}
        self._error_handlers_by_exception: typing.List[typing.Tuple[typing.Any, ErrorHandler]] = []

        # Add default handler for http exception
        self.add_error_handler(HTTPException, _http_exception_handler)

        # Set proxy object to point to current app.
        current_app._wrap(self)

    def __call__(self, scope: ASGIScope) -> ASGIAppInstance:
        '''
        Applications are instantiated with a connection scope, and then run in an event loop where they are expected
        to handle events and send data back to the client. Whenever there is a new connection, the ASGI protocol
        server calls the application instance.
        '''
        return self._dispatch(scope)

    def _dispatch(self, scope: ASGIScope) -> ASGIAppInstance:
        '''
        Create an ASGI app instance and return it.
        '''

        from bluepark.asgiapps import ASGIHTTPApplication

        if scope['type'] == 'http':
            return ASGIHTTPApplication(self, scope)

    @property
    def http_middleware_list(self):
        return self._http_middleware

    def add_http_middleware(self, middleware: HTTPMiddleware):
        self._http_middleware.append(middleware)

    def add_router(self, router: Router) -> None:
        '''Register a new router to app.'''
        router._set_main_router(self.router)

    def error_handler_by_code(self, status_code: int) -> typing.Optional[ErrorHandler]:
        '''Return error handler function or None for given HTTP status code'''
        return self._error_handlers_by_code.get(status_code, None)

    def error_handler_by_exception(self, e: Exception) -> typing.Optional[ErrorHandler]:
        '''Return error handler function or None for given exception object'''

        # Closest handler function and its distance in class hierarchy to given exception
        closest_handler = (None, 999)
        error_type = type(e)

        for e_class, handler in self._error_handlers_by_exception:
            if not isinstance(e, e_class):
                continue
            if error_type == e_class:
                closest_handler = (handler, 0)
                break
            distance = self._distance_to_parent(error_type, e_class)
            if distance < closest_handler[1]:
                closest_handler = (handler, distance)
        return closest_handler[0]

    def _distance_to_parent(self, cls, parent_cls) -> int:
        '''Breadth first search for finding the distance of parent class in inheritance hierarchy'''
        # FIFO queue for class, distance pairs
        bases_fifo = [(base, 1) for base in cls.__bases__]

        while True:
            if len(bases_fifo) == 0:
                return 999
            base_pair = bases_fifo.pop(0)
            current_cls = base_pair[0]
            current_distance = base_pair[1]
            if current_cls == parent_cls:
                return current_distance

            for base_cls in current_cls.__bases__:
                # omit object type
                if base_cls != object:
                    bases_fifo.append((base_cls, current_distance + 1))

    def add_error_handler(self, indicator: typing.Union[int, typing.Type[Exception]], handler: ErrorHandler) -> None:
        '''Add an error handler for an exception either by status code (for HTTPExceptions) or exception class'''
        if isinstance(indicator, int):
            self._error_handlers_by_code[indicator] = handler
        elif issubclass(indicator, Exception):
            self._error_handlers_by_exception.append((indicator, handler))
        else:
            raise TypeError('Indicator must be either a type of int or Exception')
