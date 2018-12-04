from typing import Awaitable

from .request import HttpRequest
from .response import HttpResponse


async def receive_http_body_middleware(request: HttpRequest, response: HttpResponse) -> None:
    '''Receive the http body and append it to the request body'''
    has_more_body = True
    body = b''
    while has_more_body:
        message = await request.receive()
        # TODO, handle other types
        if message['type'] == 'http.request':
            body += message.get('body', b'')
        has_more_body = message.get('has_more_body', False)
    request._body = body
