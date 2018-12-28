'''
28.12.2018 18:30 /arbCnH
28.12.2018 20:30  /6c9nGT
29.12.2018 13:30 /arbCnH
29.12.2018 18:30  /6c9nGT
'''
import uvicorn

from bluepark.app import BluePark
from bluepark.response import JSONResponse, TextResponse
from bluepark.routing import Router
from bluepark.session.backend import CookieSession
from bluepark.session.middleware import session_middleware
from bluepark.exceptions import HTTPException, HTTP405

app = BluePark()

user_router = Router()
blue_router = Router(prefix='/api/v1/')
app.add_router(user_router)
app.add_router(blue_router)


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


async def error_handler_403(request, e):
    return JSONResponse({
        'code': e.status_code,
        'error': e.message
    })


async def error_handler_404(request, e):
    return JSONResponse({
        'code': e.status_code,
        'error': 'Requested page is not found'
    })

app.add_error_handler(403, error_handler_403)
app.add_error_handler(404, error_handler_404)


@app.router.route('/', methods=['GET'])
async def main_page(request):
    raise HTTPException(status_code=403, message='Forbidden')


@blue_router.route('/users/<int:id>/', methods=['GET', 'POST'])
async def user_list_view(request, id):
    if id == 10:
        return TextResponse('User number 10')
    else:
        return TextResponse('User not found', status=404)


@blue_router.route('/users/<int:id>/dragons/<str:name>/', methods=['GET', 'POST'])
async def user_list_view(request, id, name):
    return TextResponse(f'User {id} and dragon {name}')


@blue_router.route('/products/', methods=['GET'])
async def product_list(request, ):
    print(request.session.items())
    request.session['visits'] = request.session.get('visits', 0) + 1
    return JSONResponse(content={})


if __name__ == "__main__":
    uvicorn.run(app, "127.0.0.1", 8000, log_level="info")
