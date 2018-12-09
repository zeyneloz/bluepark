import uvicorn

from bluepark.app import BluePark
from bluepark.routing import Router


app = BluePark()

user_router = Router()
app.register_router(user_router)
app.register_router(user_router)


@user_router.route('users/', methods=['GET', 'POST'])
async def user_list_view(request, response):
    # Visit http://localhost:8000/users/
    print(request.method)
    await response.send_text('Because love, ', more_body=True)
    await response.send_text('it’s not an emotion.', more_body=True)
    await response.send_text('Love is a promise')

if __name__ == "__main__":
    uvicorn.run(app, "127.0.0.1", 8000, log_level="info")
