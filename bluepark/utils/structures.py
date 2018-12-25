class CaseInsensitiveDict(dict):
    _init_mod = True

    def _k(self, key):
        if self._init_mod:
            return key
        return key.lower()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._init_mod = True
        self._convert_keys()
        self._init_mod = False

    def __getitem__(self, key):
        return super().__getitem__(self._k(key))

    def __setitem__(self, key, value):
        return super().__setitem__(self._k(key), value)

    def __delitem__(self, key):
        print(key)
        return super().__delitem__(self._k(key))

    def __contains__(self, key):
        return super().__contains__(self._k(key))

    def pop(self, key, *args, **kwargs):
        return super().pop(self._k(key), *args, **kwargs)

    def get(self, key, *args, **kwargs):
        return super().get(self._k(key), *args, **kwargs)

    def setdefault(self, key, *args, **kwargs):
        return super().setdefault(self._k(key), *args, **kwargs)

    def _convert_keys(self):
        for key in self.keys():
            value = self.pop(key)
            self.__setitem__(key.lower(), value)
