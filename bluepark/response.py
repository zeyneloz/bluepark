from .app import BluePark
from .types import ASGIScope, ASGISend


class HttpResponse:

    def __init__(self, app: BluePark, scope: ASGIScope, send: ASGISend) -> None:
        self.app = app
        self.scope = scope
        self.send = send

    def send_json(self):
        raise NotImplementedError()
