from .app import BluePark
from .request import HttpRequest
from .response import HttpResponse
from .utils.types import ASGIScope, ASGIReceive, ASGISend


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


class ASGIHttpApplication(BaseASGIApplication):
    '''
    ASGI app for Http connections.

    HTTP connections have a single-request connection scope - that is, your applications will be instantiated at
    the start of the request, and destroyed at the end, even if the underlying socket is still open and serving
    multiple requests.
    '''

    async def handle_connection(self):
        '''This method will be called whenever there is a new connection from ASGI server'''
        self.request = HttpRequest(self.app, self.scope, self.receive)
        self.response = HttpResponse(self.app, self.scope, self.send)

        # Run all middleware and wait for them
        await self._run_middleware()

        # TODO Remove all the code below
        # print(self.request.headers)
        # print(self.request.scope)
        # print(self.request.content_type)
        # print(self.request.body_as_json(silent=True))
        print(self.request.cookies)

        await self.response.send({
            'type': 'http.response.start',
            'status': 200,
            'headers': [
                [b'content-type', b'text/plain'],
            ]
        })
        await self.response.send({
            'type': 'http.response.body',
            'body': b'Hello, world!',
        })

    async def _run_middleware(self):
        '''Execute each middleware in http middleware list in order and await for all of them'''
        for middleware in self.app._http_middleware:
            await middleware(self.request, self.response)
