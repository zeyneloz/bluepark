import typing

from .app import BluePark
from .request import HTTPRequest
from .response import HTTPBaseResponse
from .utils.types import ASGIScope, ASGIReceive, ASGISend, HTTPView, ASGIHeaders, ErrorHandler
from .exceptions import HTTPException, HTTP404, HTTP405


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
        '''
        The receive awaitable provides events as dicts as they occur, and the send awaitable sends events back to
        the client in a similar dict format.
        '''

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

    async def start_response(self, status: int, headers: ASGIHeaders) -> None:
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

    async def end_response(self) -> None:
        '''End the http response. It is not possible to send http messages after calling this method.'''
        await self.send_http_body(b'', more_body=False)

    async def handle_connection(self) -> None:
        '''This method will be called whenever there is a new connection from ASGI server'''
        self.request = HTTPRequest(self.app, self.scope, self.receive)

        # Run all middleware and wait for them
        response = await self.dispatch()
        await self.send_response(response)

    async def dispatch(self) -> HTTPBaseResponse:
        '''Dispatch the incoming request to the view through middleware and get the response'''
        dispatcher = HTTPDispatcher(self)
        return await dispatcher()

    async def send_response(self, response: HTTPBaseResponse) -> None:
        await self.start_response(status=response.status, headers=response.get_headers())
        await self.send_http_body(body=response.body_as_bytes())


class HTTPDispatcher:
    '''Await for first middleware in the middleware list.

    Pass a callable to the middleware that returns the next middleware on the list.
    If there is no next middleware, return the view function.
    '''
    _middleware_iterator = None

    def __init__(self, asgi_app: ASGIHTTPApplication) -> None:
        self.asgi_app = asgi_app
        self._middleware_iterator = iter(asgi_app.app._http_middleware)

    async def __call__(self, *args, **kwargs) -> HTTPBaseResponse:
        '''Call the next middleware in the list and return the awaitable.'''

        # Call all middleware in order and await for their response
        next_middleware = next(self._middleware_iterator, None)
        if next_middleware is not None:
            try:
                response = await next_middleware(self.asgi_app.request, self)
            except Exception as e:
                handler = self.get_exception_handler_or_raise(e)
                return await handler(self.asgi_app.request, e)
            else:
                return response

        # At this point, all of the middleware are called and it is time to call view function
        view_function, extra_kwargs = self.get_view_function()
        try:
            response = await view_function(self.asgi_app.request, **extra_kwargs)
        except Exception as e:
            handler = self.get_exception_handler_or_raise(e)
            return await handler(self.asgi_app.request, e)
        else:
            return response

    def get_view_function(self) -> typing.Tuple[HTTPView, dict]:
        '''Return the view function that matches request path and URL param values.'''
        rule = self.asgi_app.app.router.get_rule_for_path(self.asgi_app.request.path)

        if rule is None:
            raise HTTP404()

        if not rule.is_method_allowed(self.asgi_app.request.method):
            raise HTTP405()

        # Parsed params contains the dictionary of captured URL parameter and values
        return rule.view_function, rule.parsed_params

    def get_exception_handler_or_raise(self, e: Exception) -> ErrorHandler:
        # If a exception is processed, it means that it is already captured by another middleware
        # and the handler for that exception is not found. There is no point in searching handler again.
        if getattr(e, '._processed', False):
            raise e

        # Mark Exception as processed.
        e._processed = True

        if isinstance(e, HTTPException):
            status_code = getattr(e, 'status_code', -1)
            handler = self.asgi_app.app.error_handler_by_code(status_code)
            if handler is not None:
                return handler

        handler = self.asgi_app.app.error_handler_by_exception(e)
        if handler is not None:
            return handler
        raise e
