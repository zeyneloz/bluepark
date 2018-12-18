import typing
from .backend import BaseSession


class session_middleware:

    def __init__(self, backend: typing.Type[BaseSession]):
        self.backend_class = backend

    async def __call__(self, request, response, next_middleware):
        session_cookie_name = request.app.settings['SESSION_COOKIE_NAME']
        session_cookie_string = request.cookies.get(session_cookie_name)
        request.session = self.backend_class(request.app.settings['SESSION_SECRET_KEY'])
        request.session.load(session_cookie_string)
        await next_middleware()


