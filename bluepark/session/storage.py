from bluepark.utils.signing import TimeStampedHMACSigner


class BaseSession:
    cookie_string = None

    def __init__(self, secret_key: str):
        # Holds the session data
        self._session = {}
        self.secret_key = secret_key

        # Designates if any session key is changed. This flag should be set manually if
        # the value of an mutable type is changed.
        self.modified = False

    def __setitem__(self, key, value):
        self._session[key] = value
        self.modified = True

    def __getitem__(self, key):
        return self._session[key]

    def __delete__(self, key):
        del self._session[key]
        self.modified = True

    def __contains__(self, key):
        return key in self._session

    def keys(self):
        return self._session.keys()

    def values(self):
        return self._session.values()

    def items(self):
        return self._session.items()

    def clear(self):
        self._session = {}
        self.modified = True

    def pop(self, key, default=None):
        if key in self._session:
            self.modified = True
        return self._session.pop(key, default)

    def setdefault(self, key, value):
        if key in self._session:
            return self._session[key]
        self._session[key] = value
        self.modified = True
        return value

    def load(self, cookie_string: str) -> None:
        raise NotImplementedError()

    def save(self) -> None:
        raise NotImplementedError()

    def get_cookie_string(self) -> str:
        raise NotImplementedError()


class CookieSession(BaseSession):

    def load(self, cookie_string: str) -> None:
        if cookie_string is None:
            return
        signer = TimeStampedHMACSigner(key=self.secret_key)


