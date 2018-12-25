from .globals import current_app
from .routing import MainRouter, Router
from .settings import Settings, DEFAULT_SETTINGS
from .utils.types import ASGIScope, ASGIAppInstance, HTTPMiddleware


class BluePark:
    '''
    The BluePark class implements ASGI specifications.
    '''

    def __init__(self) -> None:
        # TODO, settings from a file
        self.settings = Settings(DEFAULT_SETTINGS)

        # List of middleware functions for http connections.
        self._http_middleware = []

        # Initialize main router, every router is connected to the main router.
        self._main_router = MainRouter()

        # Set proxy object to point to current app.
        current_app._wrap(self)

    def __call__(self, scope: ASGIScope) -> ASGIAppInstance:
        '''
        Applications are instantiated with a connection scope, and then run in an event loop where they are expected
        to handle events and send data back to the client. Whenever there is a new connection, the ASGI protocol
        server calls the application instance.
        '''
        return self.dispatch(scope)

    def dispatch(self, scope: ASGIScope) -> ASGIAppInstance:
        '''
        Create an ASGI app depending on the type of the scope.
        '''

        from bluepark.asgiapps import ASGIHTTPApplication

        if scope['type'] == 'http':
            return ASGIHTTPApplication(self, scope)

    @property
    def http_middleware_list(self):
        return self._http_middleware

    def add_http_middleware(self, middleware: HTTPMiddleware):
        self._http_middleware.append(middleware)

    def register_router(self, router: Router) -> None:
        '''Register a new router to app.'''
        router._set_main_router(self._main_router)
