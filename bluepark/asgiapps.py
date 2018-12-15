from typing import Awaitable

from .app import BluePark
from .request import HTTPRequest
from .response import HTTPResponse
from .utils.types import ASGIScope, ASGIReceive, ASGISend, HTTPView


class BaseASGIApplication:
    '''
    Base class for creating ASGI applications.

    Each application instance maps to a single incoming “socket” or connection, and is expected to last the lifetime
    of that connection plus a little longer if there is cleanup to do. Some protocols may not use traditional sockets;
    ASGI specifications for those protocols are expected to define what the scope (instance) lifetime is and when it
    gets shut down.
    '''

    def __init__(self, app: BluePark, scope: ASGIScope) -> None:
        self.app = app
        self.scope = scope

    async def __call__(self, receive: ASGIReceive, send: ASGISend) -> None:
        '''The receive awaitable provides events as dicts as they occur, and the send awaitable sends events back to
        the client in a similar dict format.'''

        self.receive = receive
        self.send = send
        await self.handle_connection()

    async def handle_connection(self):
        raise NotImplementedError()


class ASGIHTTPApplication(BaseASGIApplication):
    '''
    ASGI app for Http connections.

    HTTP connections have a single-request connection scope - that is, your applications will be instantiated at
    the start of the request, and destroyed at the end, even if the underlying socket is still open and serving
    multiple requests.
    '''

    async def handle_connection(self):
        '''This method will be called whenever there is a new connection from ASGI server'''
        self.request = HTTPRequest(self.app, self.scope, self.receive)
        self.response = HTTPResponse(self.app, self.scope, self.send)

        # Run all middleware and wait for them
        await self.dispatch()

    async def dispatch(self):
        dispatcher = HTTPDispatcher(self)
        await dispatcher()


class HTTPDispatcher:
    '''Await for first middleware in the middleware list.

    Pass a callable to the middleware that returns the next middleware on the list.
    If there is no next middleware, return
    '''
    _middleware_iterator = None

    def __init__(self, asgi_app: ASGIHTTPApplication):
        self.asgi_app = asgi_app
        self._middleware_iterator = iter(asgi_app.app._http_middleware)

    def __call__(self, *args, **kwargs) -> Awaitable:
        '''Return the next middleware in the list'''

        next_middleware = next(self._middleware_iterator, None)
        if next_middleware is not None:
            return next_middleware(self.asgi_app.request, self.asgi_app.response, self)

        view_function = self.get_view_function()
        return view_function(self.asgi_app.request, self.asgi_app.response)

    def get_view_function(self) -> HTTPView:
        '''Return the view function that matches request path.
        Return None of no view is found for the path'''
        rule = self.asgi_app.app._main_router.get_rule_for_path(self.asgi_app.request.path)

        if rule is None:
            return self.not_found

        if not rule.is_method_allowed(self.asgi_app.request.method):
            return self.method_not_allowed

        return rule.view_function

    @staticmethod
    async def not_found(request, response):
        '''Send 404 Not found HTTP message'''
        response.status = 404
        await response.send_text('Not Found')

    @staticmethod
    async def method_not_allowed(request, response):
        '''Send 405 Method Not Allowed HTTP message'''
        response.status = 405
        await response.send_text('Method Not Allowed')
