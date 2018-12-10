from .app import BluePark
from .utils.types import ASGIScope, ASGISend

import json


class HttpResponse:

    def __init__(self, app: BluePark, scope: ASGIScope, send: ASGISend) -> None:
        self.app = app
        self.scope = scope
        self.send = send
        self._response_started = False
        self.headers = {}
        self.status = 200
        self.charset = app.settings['DEFAULT_RESPONSE_CHARSET']

        # charset encodings to be used
        self._header_encoding = app.settings['DEFAULT_HEADER_ENCODING']

    def _get_headers_list(self):
        '''Return the list of headers in ASGI header format.'''
        headers = []
        for name, value in self.headers.items():
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
