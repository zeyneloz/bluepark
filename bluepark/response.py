import json
import typing
from http.cookies import SimpleCookie

from . import current_app
from .exceptions import HTTPResponseAlreadyStarted
from .utils.structures import CaseInsensitiveDict
from .utils.types import ASGIHeaders


class HTTPBaseResponse:
    mime_type = None

    def __init__(self, status: int = 200, mime_type: str = None) -> None:
        self.status = status
        if mime_type is not None:
            self.mime_type = mime_type

        self._header_encoding = current_app.settings['DEFAULT_HEADER_ENCODING']
        self._response_started = False
        self.headers = CaseInsensitiveDict()
        self._extra_headers = []
        self.charset = current_app.settings['DEFAULT_RESPONSE_CHARSET']

    def get_headers(self) -> ASGIHeaders:
        '''Return the list of headers in ASGI header format.'''
        headers = []
        self.headers.setdefault('content-type', self._content_type)
        for name, value in self.headers.items():
            headers.append((name.encode(self._header_encoding), value.encode(self._header_encoding)))

        for name, value in self._extra_headers:
            headers.append((name.encode(self._header_encoding), value.encode(self._header_encoding)))
        return headers

    def set_cookie(
            self,
            key: str,
            value: str = '',
            max_age: int = None,
            expires: typing.Union[int, str] = None,
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
        self._extra_headers.append(('set-cookie', cookie_string))

    @property
    def _content_type(self):
        return f'{self.mime_type}; charset={self.charset}'

    def body_as_bytes(self) -> bytes:
        raise NotImplementedError()


class TextResponse(HTTPBaseResponse):
    mime_type = 'text/html'

    def __init__(self, content: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.content = content

    def body_as_bytes(self) -> bytes:
        return self.content.encode(self.charset)


class JSONResponse(HTTPBaseResponse):
    mime_type = 'application/json'

    def __init__(self, content: dict, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.content = content

    def body_as_bytes(self) -> bytes:
        return json.dumps(self.content, ensure_ascii=False, separators=(",", ":")).encode(self.charset)
