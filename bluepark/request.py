import json
import re
from http.cookies import SimpleCookie
from typing import Optional, AsyncGenerator

from .app import BluePark
from .exceptions import (HTTPConnectionClosed, BodyAlreadyReceived)
from .utils.decorators import cached_property
from .utils.types import ASGIScope, ASGIReceive, ASGIMessage

_media_type_from_content_type_re = re.compile(r'\s*(?P<mime>[^\s;]+)', re.I)
_charset_from_content_type_re = re.compile(r';\s*charset=(?P<charset>[^\s;]+)', re.I)
_boundary_from_content_type_re = re.compile(r';\s*boundary=(?P<boundary>[^\s;]+)', re.I)


class BaseRequest:
    headers: dict = None

    def __init__(self, app: BluePark, scope: ASGIScope, receive: ASGIReceive) -> None:
        self.app = app
        self.scope = scope
        self.receive = receive

        # charset encodings to be used
        self._header_encoding = app.settings['DEFAULT_HEADER_ENCODING']

        # a dict that holding header keys and values
        self.headers = {}

    def _parse_headers(self):
        '''
        Read all headers from the scope object and construct headers dict.

        All header names are converted to lowercase by default.
        '''
        self.headers = {header_name.decode(self._header_encoding).lower(): header_value.decode(self._header_encoding)
                        for header_name, header_value in self.scope['headers']}


class HTTPHeaderParserMixin:
    # Parsed content type header as dict
    content_type: dict = None

    # All request cookies as dict
    cookies: dict = None

    def _parse_content_type(self) -> None:
        '''Parse Content-Type header and try to get mimetype. charset, boundary.'''
        self.content_type = {}
        content_type = self.headers.get('content-type', '')

        mime_re_result = _media_type_from_content_type_re.search(content_type)
        charset_re_result = _charset_from_content_type_re.search(content_type)
        boundary_re_result = _boundary_from_content_type_re.search(content_type)

        if mime_re_result:
            self.content_type['media-type'] = mime_re_result.group('mime')
        if charset_re_result:
            self.content_type['charset'] = charset_re_result.group('charset')
        if boundary_re_result:
            self.content_type['boundary'] = boundary_re_result.group('boundary')

    def _parse_cookies(self) -> None:
        '''Parse Cookies header and build a dict.'''
        self.cookies = {}
        cookie_string = self.headers.get('cookie', '')
        cookie_parser = SimpleCookie()
        cookie_parser.load(cookie_string)

        for key, obj in cookie_parser.items():
            self.cookies[key] = obj.value

    @property
    def charset(self) -> str:
        '''Charset to be used to decode request body, designated by content-type header.'''
        return self.content_type.get('charset', self.app.settings['DEFAULT_REQUEST_CHARSET'])

    @property
    def media_type(self) -> Optional[str]:
        '''Return the media-type of the request designated by content-type header.'''
        return self.content_type.get('media-type', None)

    @cached_property
    def content_length(self) -> Optional[int]:
        '''Return CONTENT-LENGTH header as int or None.'''
        content_length = self.headers.get('content-length', None)

        if content_length is not None:
            try:
                return max(0, int(content_length))
            except (ValueError, TypeError):
                pass
        return None

    @property
    def _form_boundary(self) -> Optional[str]:
        return self.content_type.get('boundary', None)


class BaseHTTPRequest(BaseRequest, HTTPHeaderParserMixin):
    # Boolean value signifying if there is additional content to come (as part of a Request message
    _has_more_body = True

    # All http body in bytes
    body: bytes = None

    # Body as string
    text: str = None

    # Body as json object
    json: dict = None

    def __init__(self, app: BluePark, scope: ASGIScope, receive: ASGIReceive) -> None:
        super().__init__(app, scope, receive)

        # Order of the method calls below is important.
        self._parse_scope()
        self._parse_headers()
        self._parse_content_type()
        self._parse_cookies()

    def _parse_scope(self) -> None:
        '''Define ASGI attributes for the request'''

        self.method = self.scope.get('method', '')
        self.scheme = self.scope.get('scheme', 'http')
        self.http_version = self.scope.get('http_version', '1.1')
        self.path = self.scope.get('path')
        self.query_string = self.scope.get('query_string', b'').decode(self._header_encoding)
        self.full_path = self.path + self.query_string
        self.script_path = self.scope.get('root_path', '')

    async def next_http_message(self) -> ASGIMessage:
        '''Receive and return next http message. Raise exception if the connection is closed.'''
        if not self._has_more_body:
            raise BodyAlreadyReceived()

        message = await self.receive()
        if message['type'] == 'http.disconnect':
            raise HTTPConnectionClosed()
        if message['type'] == 'http.request':
            return message
        # Return fake message on unknown message type
        return {}

    async def stream_http_body(self) -> AsyncGenerator[bytes, None]:
        '''Await for next http message and yield the body until `has_more_body` is False.'''
        while self._has_more_body:
            message = await self.next_http_message()
            self._has_more_body = message.get('has_more_body', False)
            yield message.get('body', b'')

    async def receive_http_body(self) -> None:
        '''Receive and assemble http body.'''
        if not self._has_more_body:
            raise BodyAlreadyReceived()

        self.body = b''
        async for body in self.stream_http_body():
            self.body += body

    async def body_as_bytes(self) -> Optional[bytes]:
        '''
        Receive all HTTP messages and return the body. Cache the result in `self.body`.
        '''
        if self.body is None:
            await self.receive_http_body()
        return self.body

    async def body_as_text(self, silent=False) -> Optional[str]:
        '''
        Decode and return the request body using `self.charset`. Cache the result in `self.text`.

        :param silent: Do not raise decoding errors and return `None` instead.
        '''
        if self.text is None:
            try:
                body = await self.body_as_bytes()
                self.text = body.decode(self.charset)
            except UnicodeDecodeError as e:
                if silent:
                    return None
                else:
                    raise e

        return self.text

    async def body_as_json(self, silent=False) -> Optional[dict]:
        '''
        Parse request body as JSON and return. Cache the return value in `self.json`.

        :param silent: Do not raise parsing errors and return `None` instead.
        '''
        if self.json is None:
            try:
                text = await self.body_as_text(silent=silent)
                self.json = json.loads(text)
            except (ValueError, TypeError) as e:
                if silent:
                    return None
                else:
                    raise e

        return self.json


class HTTPRequest(BaseHTTPRequest):
    '''HTTP 1.1 Request'''
    pass
