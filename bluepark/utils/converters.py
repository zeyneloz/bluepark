import uuid


class BaseConverter:
    '''Converter for routing'''
    # Regex pattern to use to match this converter
    regex = ''

    def value(self, value: str):
        raise NotImplementedError()


class IntConverter(BaseConverter):
    regex = '[0-9]+'

    def value(self, value: str) -> int:
        return int(value)


class StringConverter(BaseConverter):
    regex = '[^/]+'

    def value(self, value: str) -> str:
        return value


class PathConverter(StringConverter):
    regex = '.+'


class UUIDConverter(BaseConverter):
    regex = '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'

    def value(self, value: str) -> uuid.UUID:
        return uuid.UUID(value)


CONVERTERS = {
    'int': IntConverter(),
    'str': StringConverter(),
    'path': PathConverter(),
    'uuid': UUIDConverter()
}
