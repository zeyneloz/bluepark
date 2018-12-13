from http.cookies import SimpleCookie
import json
from typing import Union

from .app import BluePark
from .utils.types import ASGIScope, ASGISend
from .exceptions import HTTPResponseAlreadyStarted


class HttpResponse:

    def __init__(self, app: BluePark, scope: ASGIScope, send: ASGISend) -> None:
        self.app = app
        self.scope = scope
        self.send = send
        self._response_started = False
        self.headers = {}
        self._extra_headers = []
        self.status = 200
        self.charset = app.settings['DEFAULT_RESPONSE_CHARSET']

        # charset encodings to be used
        self._header_encoding = app.settings['DEFAULT_HEADER_ENCODING']

    def _get_headers_list(self):
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
        await self.send({
            'type': 'http.response.start',
            'status': self.status,
            'headers': self._get_headers_list()
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

    async def send_text(self, text, more_body: bool = False) -> None:
        '''
        Send text response.

        :param text: Text to be sent
        :param more_body: If it is True, does not end the response and more body can be sent.
        '''

        self.headers['Content-Type'] = f'text/plain; charset={self.charset}'
        await self.start_response()
        await self.send_http_body(text.encode(self.charset), more_body=more_body)

    async def send_json(self, json_obj):
        '''
        Send JSON response.

        :param json_obj: Dictionary object to be sent.
        '''
        self.headers['Content-Type'] = f'application/json; charset={self.charset}'
        json_body = json.dumps(json_obj, ensure_ascii=False, separators=(",", ":"))
        await self.start_response()
        await self.send_http_body(json_body.encode(self.charset))

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
