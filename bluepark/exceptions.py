
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
