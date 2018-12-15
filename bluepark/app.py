from .routing import MainRouter, Router
from .settings import Settings, DEFAULT_SETTINGS
from .utils.types import ASGIScope, ASGIAppInstance


class BluePark:
    '''
    The BluePark class implements ASGI specifications.
    '''

    def __init__(self) -> None:
        self.settings = Settings(DEFAULT_SETTINGS)
        self._http_middleware = []
        self._main_router = MainRouter()

    def __call__(self, scope: ASGIScope) -> ASGIAppInstance:
        # scope is a dictionary that contains at least a type key specifying the protocol that is incoming.
        return self.dispatch(scope)

    def dispatch(self, scope: ASGIScope) -> ASGIAppInstance:
        '''This method creates an ASGI app'''

        from bluepark.asgiapps import ASGIHTTPApplication

        if scope['type'] == 'http':
            return ASGIHTTPApplication(self, scope)

    @property
    def http_middleware_list(self):
        return self._http_middleware

    def add_http_middleware(self, middleware):
        self._http_middleware.append(middleware)

    def register_router(self, router: Router) -> None:
        '''Register a new router to app.'''
        router._set_main_router(self._main_router)
