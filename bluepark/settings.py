from typing import Optional

DEFAULT_SETTINGS = {
    'DEBUG': False,
    'ENV': None,

    # Default charset to be used in decoding of request body
    'DEFAULT_REQUEST_CHARSET': 'utf-8',

    # Default charset to be used in encoding of response body
    'DEFAULT_RESPONSE_CHARSET': 'utf-8',

    # Default charset encoding to be used in decoding of request headers
    'DEFAULT_HEADER_ENCODING': 'latin-1',

    # Secret key to be used sign session cookies
    'SESSION_SECRET_KEY': 'When',
    
    # Name to be used in cookies for session
    'SESSION_COOKIE_NAME': 'session',

    # In seconds, defaults to 15 days
    'SESSION_COOKIE_MAX_AGE': 60 * 60 * 24 * 15,

    # The path set on the session cookie
    'SESSION_COOKIE_PATH': '/',

    # Makes cookies inaccessible by javascript code
    'SESSION_COOKIE_HTTPONLY': True


}


class Settings(dict):

    def __init__(self, defaults: Optional[dict]) -> None:
        super(Settings, self).__init__(defaults or {})

