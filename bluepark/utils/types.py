import typing


# Scope is a dictionary that contains at least a type key specifying the protocol that is incoming.
ASGIScope = typing.Mapping[str, typing.Any]

# Every ASGI message
ASGIMessage = typing.Dict[str, typing.Any]
ASGIReceive = typing.Callable[[], typing.Awaitable[ASGIMessage]]
ASGISend = typing.Callable[[ASGIMessage], typing.Awaitable[None]]
ASGIAppInstance = typing.Callable[[ASGIReceive, ASGISend], typing.Awaitable[None]]
ASGIApp = typing.Callable[[ASGIScope], ASGIAppInstance]
ASGIHeaders = typing.List[typing.Tuple[bytes, bytes]]
HTTPResponse = typing.Any

HTTPView = typing.Callable[[typing.Any], typing.Awaitable[HTTPResponse]]
ErrorHandler = typing.Callable[[typing.Any, Exception], typing.Awaitable[HTTPResponse]]
HTTPMiddleware = typing.Callable[[typing.Any, typing.Any], typing.Awaitable[HTTPResponse]]
RequestMethods = typing.Iterable[str]
