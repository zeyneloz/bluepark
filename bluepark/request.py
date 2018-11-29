import typing

from bluepark.types import ASGIScope, ASGIReceive


class BaseRequest:

    def __init__(self, scope: ASGIScope, receive: ASGIReceive) -> None:
        self._scope = scope
        self._receive = receive
        self._has_more_body = True

    @property
    def scope(self) -> ASGIScope:
        return self._scope

    def _parse_headers(self):
        '''Read all headers from the scope object and construct headers dict'''
        return {header_name.decode(): header_value.decode()
                for header_name, header_value in self._scope['headers']}

    async def _read_body(self) -> typing.AsyncGenerator[bytes, None]:
        '''Read the current chunk in body and yield it'''
        while self._has_more_body:
            message = await self._receive()
            body = message.get('body', b'')
            self._has_more_body = message.get('more_body', False)
            yield body
        yield b''


class HttpRequest(BaseRequest):

    def __init__(self, scope: ASGIScope, receive: ASGIReceive) -> None:
        super(HttpRequest, self).__init__(scope, receive)
        self._body = None
        self._headers = self._parse_headers()

    @property
    def scope(self) -> ASGIScope:
        return self._scope

    @property
    def headers(self) -> dict:
        return self._headers

    async def body(self) -> bytes:
        '''Read and return the entire body from an incoming ASGI request. Cache the body for later access'''
        if self._body is None:
            self._body = b''
            async for body_chunk in self._read_body():
                self._body += body_chunk
        return self._body
