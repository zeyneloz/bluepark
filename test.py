# 23.09.2016 /zCkwrF
import uvicorn

from bluepark.app import BluePark
from bluepark.routing import Router
from bluepark.session.middleware import session_middleware
from bluepark.session.backend import CookieSession
from bluepark.response import JSONBody, TextBody

app = BluePark()

user_router = Router()
blue_router = Router(prefix='api/v1/')
app.register_router(user_router)
app.register_router(blue_router)


async def middleware_logger(request, response, next_middleware):
    print(f'New request for: {request.method} - {request.path}')
    await next_middleware()
    print('Request ends')

# Middleware are called in order before calling the view function
# Every middleware must await for next_middleware
# At the end, next_middleware will reach the view function.
app.add_http_middleware(middleware_logger)
app.add_http_middleware(session_middleware(backend=CookieSession))


@user_router.route('speech/', methods=['GET', 'POST'])
async def user_list_view(request, response):
    response.set_cookie(key='csrf', value='7 months', max_age=3600)
    response.body = TextBody(data='Love is a promise?')


@blue_router.route('users/', methods=['GET'])
async def user_list(request, response):
    if request.method == 'GET':
        response.body = JSONBody(data={
            'bucket-list': [
                {'id': 1, 'todo': '/'},
                {'id': 2, 'todo': '3'},
                {'id': 3, 'todo': 'a'},
                {'id': 4, 'todo': 'j'},
                {'id': 5, 'todo': '1'},
                {'id': 6, 'todo': 'v'},
                {'id': 7, 'todo': 'C'},
            ]
        })


@blue_router.route('products/', methods=['GET'])
async def product_list(request, response):
    response.body = JSONBody(data={})

if __name__ == "__main__":
    uvicorn.run(app, "127.0.0.1", 8000, log_level="info")
