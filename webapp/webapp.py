import uvicorn

from multiprocessing import Queue
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .routers import items, users, admin
from .internal import security


class WebApp:
    def __init__(self, p_q: Queue):
        self.p_q = p_q
        self.test_data = "cube"

    def run(self):
        app = FastAPI()
        app.p_q = self.p_q

        app.mount("/ui/", StaticFiles(directory="./webapp/static/ui", html=True), name="ui")

        app.include_router(security.router)
        app.include_router(users.router)
        app.include_router(items.router)
        app.include_router(admin.router)

        # @app.get("/")
        # async def root():
        #     action = {
        #         "target": "main",
        #         "action": "main_restart",
        #         "payload": "",
        #         "source": "webui",
        #     }
        #     self.p_q.put(action)
        #
        #     return {"message": self.test_data}

        uvicorn.run(app, host="127.0.0.1", port=8080, log_level="info")
