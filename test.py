# 23.09.2016 /zCkwrF
import uvicorn

from bluepark.app import BluePark
from bluepark.routing import Router


app = BluePark()

user_router = Router()
blue_router = Router(prefix='api/v1/')
app.register_router(user_router)
app.register_router(blue_router)


async def middleware_logger(request, response, next_middleware):
    print(f'New request for: {request.path}')
    await next_middleware()
    print('Returned from  middleware_cookie')


async def middleware_cookie(request, response, next_middleware):
    response.set_cookie('sessionid', 'f9Kw2a', 10*8*2016)
    print('Session id is set')
    await next_middleware()
    print('Returned from view function')

# Middleware are called in order before calling the view function
# Every middleware must await for next_middleware
# At the end, next_middleware will reach the view function.
app.add_http_middleware(middleware_logger)
app.add_http_middleware(middleware_cookie)


@user_router.route('speech/', methods=['GET', 'POST'])
async def user_list_view(request, response):
    # Visit http://localhost:8000/speech/
    print(request.method)
    await response.send_text('Because love, ', more_body=True)
    await response.send_text('it’s not an emotion.', more_body=True)
    await response.send_text('Love is a promise')


@blue_router.route('users/', methods=['GET', 'POST'])
async def user_list(request, response):
    if request.method == 'GET':
        response.set_cookie(key='csrf', value='frr8Uw', max_age=3600)
        response.set_cookie(key='token', value='SJS7JMZ02PPXYEGKHLQ1FFF', max_age=60*60*60)
        return await response.send_json([
            {'id': 1, 'name': 'zeynel'},
            {'id': 2, 'name': 'was'},
            {'id': 3, 'name': 'here'}
        ])
    await response.send_json({})


@blue_router.route('products/', methods=['GET'])
async def product_list(request, response):
    from bluepark import current_app
    print(current_app.settings)
    await response.send_json([
        {'id': 1, 'name': 'never'}
    ])

if __name__ == "__main__":
    uvicorn.run(app, "127.0.0.1", 8000, log_level="info")
