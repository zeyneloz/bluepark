# 23.09.2016 /zCkwrF
import uvicorn

from bluepark.app import BluePark
from bluepark.response import JSONResponse, TextResponse
from bluepark.routing import Router
from bluepark.session.backend import CookieSession
from bluepark.session.middleware import session_middleware

app = BluePark()

user_router = Router()
blue_router = Router(prefix='/api/v1/')
app.register_router(user_router)
app.register_router(blue_router)


async def middleware_logger(request, next_middleware):
    print(f'New request for: {request.method} - {request.path}')
    response = await next_middleware()
    print('Request ends')
    return response


# Middleware are called in order before calling the view function
# Every middleware must await for next_middleware
# At the end, next_middleware will reach the view function.
app.add_http_middleware(middleware_logger)
app.add_http_middleware(session_middleware(backend=CookieSession))


@user_router.route('/', methods=['GET'])
async def main_page(request):
    return TextResponse('Main page', status=200)


@user_router.route('/speech/', methods=['GET', 'POST'])
async def user_list_view(request):
    response = TextResponse('Okay', status=200)
    response.set_cookie(key='csrf', value='r', max_age=3600)
    return response


@blue_router.route('/users/', methods=['GET'])
async def user_list(request):
    if request.method == 'GET':
        return JSONResponse({
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


@blue_router.route('/products/', methods=['GET'])
async def product_list(request, ):
    print(request.session.items())
    request.session['visits'] = request.session.get('visits', 0) + 1
    return JSONResponse(content={})


if __name__ == "__main__":
    uvicorn.run(app, "127.0.0.1", 8000, log_level="info")
