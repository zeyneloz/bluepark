

class CaseInsensitiveDict(dict):

    def __init__(self, *args, **kwargs):
        super(CaseInsensitiveDict, self).__init__(*args, **kwargs)
        self._convert_keys()

    def __getitem__(self, key):
        return super().__getitem__(key.lower())

    def __setitem__(self, key, value):
        return super().__setitem__(key.lower(), value)

    def __delitem__(self, key):
        return super().__delitem__(key.lower())

    def __contains__(self, key):
        return super().__contains__(key.lower())

    def has_key(self, key):
        return super().has_key(key.lower())

    def pop(self, key, *args, **kwargs):
        return super().pop(key.lower(), *args, **kwargs)

    def get(self, key, *args, **kwargs):
        return super().get(key.lower(), *args, **kwargs)

    def setdefault(self, key, *args, **kwargs):
        return super().setdefault(key.lower(), *args, **kwargs)

    def _convert_keys(self):
        for key in self.keys():
            value = self.pop(key)
            self.__setitem__(key, value)
