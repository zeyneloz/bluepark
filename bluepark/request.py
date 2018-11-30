import json

from .app import BluePark
from .utils import cached_property
from .types import ASGIScope, ASGIReceive


class BaseRequest:

    def __init__(self, app: BluePark, scope: ASGIScope, receive: ASGIReceive) -> None:
        self.app = app
        self.scope = scope
        self.receive = receive

        # charset encodings to be used
        self._header_encoding = app.settings['DEFAULT_HEADER_ENCODING']
        self._charset_encoding = app.settings['DEFAULT_CHARSET_ENCODING']

    @property
    def charset_encoding(self):
        return self._charset_encoding

    def _parse_headers(self):
        '''
        Read all headers from the scope object and construct headers dict.

        All header names are converted to uppercase by default.
        '''
        return {header_name.decode(self._header_encoding).upper(): header_value.decode(self._header_encoding)
                for header_name, header_value in self.scope['headers']}


class HttpRequest(BaseRequest):
    '''HTTP 1.1 Request'''

    def __init__(self, app: BluePark, scope: ASGIScope, receive: ASGIReceive) -> None:
        super(HttpRequest, self).__init__(app, scope, receive)

        self._has_more_body = True
        self._body = None
        self._json = None
        self.method = None
        self.cookies = None

        self._parse_scope()

    def _parse_scope(self):
        self.headers = self._parse_headers()
        self.method = self.scope.get('method', None)
        self.scheme = self.scope.get('scheme', 'http')
        self.http_version = self.scope.get('http_version', None)
        self.path = self.scope.get('path')
        self.query_string = self.scope.get('query_string', b'').decode(self._header_encoding)
        self.full_path = self.path + self.query_string

    @cached_property
    def body_as_bytes(self) -> bytes:
        return self._body

    @cached_property
    def body_as_text(self) -> str:
        return self.body_as_bytes.decode(self.charset_encoding)

    @cached_property
    def body_as_json(self) -> str:
        return json.loads(self.body_as_text)
