import typing

ASGIScope = typing.Mapping[str, typing.Any]
ASGIMessage = typing.Dict[str, typing.Any]
ASGIReceive = typing.Callable[[], typing.Awaitable[ASGIMessage]]
ASGISend = typing.Callable[[ASGIMessage], typing.Awaitable[None]]
ASGIAppInstance = typing.Callable[[ASGIReceive, ASGISend], typing.Awaitable[None]]
ASGIApp = typing.Callable[[ASGIScope], ASGIAppInstance]

HttpMiddleware = typing.Callable[[], typing.Awaitable]
