from .handlers import HttpHandler
from .types import ASGIScope, ASGIAppInstance


class BluePark:
    '''
    The BluePark class implements ASGI specifications.
    '''

    def __init__(self) -> None:
        pass

    def __call__(self, scope: ASGIScope) -> ASGIAppInstance:
        # scope is a dictionary that contains at least a type key specifying the protocol that is incoming.
        return self.dispatch(scope)

    def dispatch(self, scope: ASGIScope) -> ASGIAppInstance:
        '''This method should create an ASGI app for every request coming by their scope type.'''
        if scope['type'] == 'http':
            return HttpHandler(scope)
