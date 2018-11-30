from .settings import Settings, DEFAULT_SETTINGS
from .types import ASGIScope, ASGIAppInstance


class BluePark:
    '''
    The BluePark class implements ASGI specifications.
    '''

    def __init__(self) -> None:
        self.settings = Settings(DEFAULT_SETTINGS)
        self._http_middleware = []

    def __call__(self, scope: ASGIScope) -> ASGIAppInstance:
        # scope is a dictionary that contains at least a type key specifying the protocol that is incoming.
        return self.dispatch(scope)

    def dispatch(self, scope: ASGIScope) -> ASGIAppInstance:
        '''This method creates an ASGI app'''

        from .applications import ASGIHttpApplication

        if scope['type'] == 'http':
            return ASGIHttpApplication(self, scope)

    @property
    def http_middleware_list(self):
        return self._http_middleware

    def add_http_middleware(self, middleware):
        self._http_middleware.append(middleware)
