from .request import HttpRequest
from .types import ASGIScope, ASGIReceive, ASGISend


class HttpHandler:
    '''
    ASGI app for Http connections.

    HTTP connections have a single-request connection scope - that is, your applications will be instantiated at
    the start of the request, and destroyed at the end, even if the underlying socket is still open and serving
    multiple requests.
    '''

    def __init__(self, scope: ASGIScope) -> None:
        self.scope = scope

    async def __call__(self, receive: ASGIReceive, send: ASGISend) -> None:
        '''The receive awaitable provides events as dicts as they occur, and the send awaitable sends events back to
        the client in a similar dict format.'''

        request = HttpRequest(self.scope, receive)
        print(request.headers)
        print(await request.body())
        await send({
            'type': 'http.response.start',
            'status': 200,
            'headers': [
                [b'content-type', b'text/plain'],
            ]
        })
        await send({
            'type': 'http.response.body',
            'body': b'Hello, world!',
        })

    async def read_body(self, receive):
        body = await receive()
        return body
