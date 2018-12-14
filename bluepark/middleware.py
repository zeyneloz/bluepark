from typing import Awaitable

from .request import HTTPRequest
from .response import HTTPResponse


async def receive_http_body_middleware(request: HTTPRequest, response: HttpResponse) -> None:
    '''Receive the http body and append it to the request body'''
    has_more_body = True
    body = b''
    while has_more_body:
        message = await request.receive()
        # TODO, handle other types
        if message['type'] == 'http.request':
            body += message.get('body', b'')
        has_more_body = message.get('has_more_body', False)
    request._has_more_body = False
    request.body = body
