import typing

from .app import BluePark
from .request import HTTPRequest
from .response import TextResponse, HTTPBaseResponse
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
        self._response_started = False

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

    async def start_response(self, status, headers):
        '''Start the http response if it is not started yet.'''
        if self._response_started:
            return
        self._response_started = True
        await self.send({
            'type': 'http.response.start',
            'status': status,
            'headers': headers
        })

    async def send_http_body(self, body: bytes, more_body: bool = False) -> None:
        '''Send a http body message.'''
        await self.send({
            'type': 'http.response.body',
            'body': body,
            'more_body': more_body
        })

    async def end_response(self):
        '''End the http response. It is not possible to send http messages after calling this method.'''
        await self.send_http_body(b'', more_body=False)

    async def handle_connection(self):
        '''This method will be called whenever there is a new connection from ASGI server'''
        self.request = HTTPRequest(self.app, self.scope, self.receive)

        # Run all middleware and wait for them
        response = await self.dispatch()
        await self.send_response(response)

    async def dispatch(self):
        dispatcher = HTTPDispatcher(self)
        return await dispatcher()

    async def send_response(self, response: HTTPBaseResponse):
        await self.start_response(status=response.status, headers=response.get_headers())
        await self.send_http_body(body=response.body_as_bytes())


class HTTPDispatcher:
    '''Await for first middleware in the middleware list.

    Pass a callable to the middleware that returns the next middleware on the list.
    If there is no next middleware, return
    '''
    _middleware_iterator = None

    def __init__(self, asgi_app: ASGIHTTPApplication):
        self.asgi_app = asgi_app
        self._middleware_iterator = iter(asgi_app.app._http_middleware)

    def __call__(self, *args, **kwargs) -> typing.Awaitable:
        '''Return the next middleware in the list'''

        next_middleware = next(self._middleware_iterator, None)
        if next_middleware is not None:
            return next_middleware(self.asgi_app.request, self)

        view_function, extra_kwargs = self.get_view_function()
        return view_function(self.asgi_app.request, **extra_kwargs)

    def get_view_function(self) -> typing.Tuple[HTTPView, dict]:
        '''Return the view function that matches request path and URL param values.'''
        rule = self.asgi_app.app._main_router.get_rule_for_path(self.asgi_app.request.path)

        if rule is None:
            return self.not_found, {}

        if not rule.is_method_allowed(self.asgi_app.request.method):
            return self.method_not_allowed, {}

        # Parsed params contains the dictionary of captured URL parameter and values
        return rule.view_function, rule.parsed_params

    @staticmethod
    async def not_found(request):
        '''Send 404 Not found HTTP message'''
        return TextResponse('Not Found', status=404)

    @staticmethod
    async def method_not_allowed(request):
        '''Send 405 Method Not Allowed HTTP message'''
        return TextResponse('Method Not Allowed', status=404)
