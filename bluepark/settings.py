from typing import Optional

DEFAULT_SETTINGS = {
    'DEBUG': False,
    'ENV': None,

    # Default charset to be used in decoding of request body
    'DEFAULT_CHARSET_ENCODING': 'utf-8',

    # Default charset encoding to be used in decoding of request headers
    'DEFAULT_HEADER_ENCODING': 'latin-1',
}


class Settings(dict):

    def __init__(self, defaults: Optional[dict]) -> None:
        super(Settings, self).__init__(defaults or {})

