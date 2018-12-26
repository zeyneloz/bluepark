class RequestBodyNotExist(Exception):
    '''Http request body is not yet received'''
    pass


class HTTPConnectionClosed(Exception):
    '''HTTP connection is closed or if receive is called after a response has been sent'''
    pass


class BodyAlreadyReceived(Exception):
    '''All of the HTTP body is already received'''
    pass


class HTTPResponseAlreadyStarted(Exception):
    '''HTTP response already started'''
    pass


class PathRegisterError(Exception):
    '''Error while registerinf a path'''
    pass


class HTTPException(Exception):
    '''Base exception for all http errors to be handled by the error handlers'''

    status_code: int = None
    message: str = None

    def __init__(self, status_code: int = None, message: str = None):
        super().__init__(self)
        if status_code is not None:
            self.status_code = status_code

        if message is not None:
            self.message = message


class HTTP404(HTTPException):
    status_code = 404
    message = 'Not Found'


class HTTP405(HTTPException):
    status_code = 405
    message = 'Method Not Allowed'
