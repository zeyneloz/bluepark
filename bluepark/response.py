from http.cookies import SimpleCookie
import json
from typing import Union

from .app import BluePark
from .utils.types import ASGIScope, ASGISend
from .exceptions import HTTPResponseAlreadyStarted


class HTTPResponse:
    '''Response object that is passed to the middleware and view.'''

    def __init__(self, app: BluePark, scope: ASGIScope, send: ASGISend) -> None:
        self.app = app
        self.scope = scope
        self._send = send
        self._response_started = False
        self.headers = {}
        self._extra_headers = []
        self.status = 200
        self.charset = app.settings['DEFAULT_RESPONSE_CHARSET']
        self.body = None

        # charset encodings to be used
        self._header_encoding = app.settings['DEFAULT_HEADER_ENCODING']

    def _get_headers(self):
        '''Return the list of headers in ASGI header format.'''
        headers = []
        for name, value in self.headers.items():
            headers.append([name.encode(self._header_encoding), value.encode(self._header_encoding)])

        for name, value in self._extra_headers:
            headers.append([name.encode(self._header_encoding), value.encode(self._header_encoding)])
        return headers

    async def start_response(self):
        '''Start the http response if it is not started yet.'''
        if self._response_started:
            return

        self._response_started = True
        await self._send({
            'type': 'http.response.start',
            'status': self.status,
            'headers': self._get_headers()
        })

    async def send_http_body(self, body: bytes, more_body: bool = False) -> None:
        '''Send a http body message.'''
        await self._send({
            'type': 'http.response.body',
            'body': body,
            'more_body': more_body
        })

    async def end_response(self):
        '''End the http response. It is not possible to send http messages after calling this method.'''
        await self.send_http_body(b'', more_body=False)

    def set_cookie(
            self,
            key: str,
            value: str = '',
            max_age: int = None,
            expires: Union[int, str] = None,
            path: str = '/',
            domain: str = None,
            secure: bool = False,
            http_only: bool = False,
            same_site: str = None
    ):
        '''
        Sets a cookie with given params.

        :param key: The key of the cookie.
        :param value: The value of the cookie.
        :param max_age: Number of seconds. Expires cookie after that much seconds.
        :param expires: Should be a datetime object or UNIX timestamp.
        :param path: Limits the cookie to a given path.
        :param domain: Specifies allowed hosts to receive the cookie. If unspecified, it defaults to the host of the
        current document location, excluding subdomains.
        :param secure: If True, the cookie will only be available on HTTPS.
        :param http_only: If True cookies are inaccessible to JavaScript's document.cookie.
        :param same_site: Let servers require that a cookie shouldn't be sent with cross-site requests. The same-site
        attribute can have one of two values: `strict` or `lax`.
        '''
        if self._response_started:
            raise HTTPResponseAlreadyStarted("You can't set cookie after response has started")

        cookie = SimpleCookie()
        cookie[key] = value
        cookie[key]['path'] = path
        if max_age is not None:
            cookie[key]['max-age'] = max_age
        if expires is not None:
            cookie[key]['expires'] = expires
        if domain is not None:
            cookie[key]['domain'] = domain
        if secure:
            cookie[key]['secure'] = True
        if http_only:
            cookie[key]['httponly'] = True

        cookie_string = cookie.output(header='').strip()
        if same_site is not None:
            cookie_string = cookie_string.rstrip(';') + f'; SameSite={same_site}'
        self._extra_headers.append(('Set-Cookie', cookie_string))


class BaseBody:
    '''Base response body'''

    def get_body(self, charset: str):
        raise NotImplementedError()

    @property
    def mime_type(self) -> str:
        raise NotImplementedError()


class JSONBody(BaseBody):

    def __init__(self, data: dict) -> None:
        self.data = data

    def get_body(self, charset: str) -> bytes:
        return json.dumps(self.data, ensure_ascii=False, separators=(",", ":")).encode(charset)

    @property
    def mime_type(self) -> str:
        return 'application/json'


class TextBody(BaseBody):
    def __init__(self, data: str) -> None:
        self.data = data

    def get_body(self, charset: str) -> bytes:
        return self.data.encode(charset)

    @property
    def mime_type(self) -> str:
        return 'text/html'
