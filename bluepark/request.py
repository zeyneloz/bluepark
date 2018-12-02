import json
import re

from .app import BluePark
from .utils.decorators import cached_property
from .utils.types import ASGIScope, ASGIReceive


_media_type_from_content_type_re = re.compile(r'\s*(?P<mime>[^\s;]+)', re.I)
_charset_from_content_type_re = re.compile(r';\s*charset=(?P<charset>[^\s;]+)', re.I)
_boundary_from_content_type_re = re.compile(r';\s*boundary=(?P<boundary>[^\s;]+)', re.I)


class BaseRequest:

    def __init__(self, app: BluePark, scope: ASGIScope, receive: ASGIReceive) -> None:
        self.app = app
        self.scope = scope
        self.receive = receive

        # charset encodings to be used
        self._header_encoding = app.settings['DEFAULT_HEADER_ENCODING']
        self._encoding = app.settings['DEFAULT_CHARSET_ENCODING']

    def _parse_headers(self):
        '''
        Read all headers from the scope object and construct headers dict.

        All header names are converted to uppercase by default.
        '''
        self.headers = {header_name.decode(self._header_encoding).upper(): header_value.decode(self._header_encoding)
                        for header_name, header_value in self.scope['headers']}

    @property
    def encoding(self):
        '''Charset to be used to decode request body'''
        return self._encoding


class HttpRequest(BaseRequest):
    '''HTTP 1.1 Request'''

    def __init__(self, app: BluePark, scope: ASGIScope, receive: ASGIReceive) -> None:
        super(HttpRequest, self).__init__(app, scope, receive)

        self._has_more_body = True
        self._body = None
        self._json = None
        self.cookies = {}
        self.content_type = {}
        self.headers = {}

        self._parse_scope()
        self._parse_content_type()

    def _parse_scope(self):
        '''Define ASGI attributes for the request'''

        self._parse_headers()
        self.method = self.scope.get('method', '')
        self.scheme = self.scope.get('scheme', 'http')
        self.http_version = self.scope.get('http_version', '1.1')
        self.path = self.scope.get('path')
        self.query_string = self.scope.get('query_string', b'').decode(self._header_encoding)
        self.full_path = self.path + self.query_string
        self.script_path = self.scope.get('root_path', '')

    def _parse_content_type(self):
        '''Parse Content-Type header and try to get mimetype. charset, boundary'''
        content_type = self.headers.get('CONTENT-TYPE', '')
        self.content_type = {}

        mime_re_result = _media_type_from_content_type_re.search(content_type)
        charset_re_result = _charset_from_content_type_re.search(content_type)
        boundary_re_result = _boundary_from_content_type_re.search(content_type)

        if mime_re_result:
            self.content_type['media-type'] = mime_re_result.group('mime')
        if charset_re_result:
            self.content_type['charset'] = charset_re_result.group('charset')
            self._encoding = charset_re_result.group('charset')
        if boundary_re_result:
            self.content_type['boundary'] = boundary_re_result.group('boundary')

    @cached_property
    def body_as_bytes(self) -> bytes:
        return self._body

    @cached_property
    def body_as_text(self) -> str:
        return self.body_as_bytes.decode(self.charset)

    @cached_property
    def body_as_json(self) -> str:
        return json.loads(self.body_as_text)
