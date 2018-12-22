from typing import Type, Union

from bluepark.request import HTTPRequest
from bluepark.response import HTTPBaseResponse
from bluepark.utils.types import HTTPMiddleware, HTTPView
from .backend import BaseSession


class session_middleware:
    '''Add session dict to request and use backend class to store the session.'''

    def __init__(self, backend: Type[BaseSession]) -> None:
        self.backend_class = backend

    async def __call__(self, request: HTTPRequest, nxt: Union[HTTPMiddleware, HTTPView]) -> Type[HTTPBaseResponse]:
        session_cookie_name = request.app.settings['SESSION_COOKIE_NAME']
        session_cookie_string = request.cookies.get(session_cookie_name)
        request.session = self.backend_class(request.app.settings['SESSION_SECRET_KEY'])
        request.session.load(session_cookie_string)
        response = await nxt()
        if not request.session.modified:
            return response

        if not request.session.is_empty:
            request.session.save()
            response.set_cookie(
                key=request.app.settings['SESSION_COOKIE_NAME'],
                value=request.session.cookie_string,
                max_age=request.app.settings['SESSION_COOKIE_MAX_AGE'],
                path=request.app.settings['SESSION_COOKIE_PATH'],
                http_only=request.app.settings['SESSION_COOKIE_HTTPONLY']
            )
        else:
            # If the dictionary is empty, expire current session string on client.
            response.set_cookie(
                key=request.app.settings['SESSION_COOKIE_NAME'],
                value='',
                expires=0
            )
        return response
