import uvicorn

from bluepark.app import BluePark
from bluepark.middleware import receive_http_body_middleware


app = BluePark()
# app.add_http_middleware(receive_http_body_middleware)

if __name__ == "__main__":
    uvicorn.run(app, "127.0.0.1", 8000, log_level="info")
