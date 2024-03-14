import uvicorn

from multiprocessing import Queue
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .routers import admin, chat, custom, pet, mod
from .internal import security

from repo import Repo


class WebApp:
    def __init__(self, p_q: Queue):
        self.p_q = p_q
        self.test_data = "cube"

    def run(self):
        app = FastAPI(
            responses={
                204: {"description": "Request is valid but no matching content found."},
                404: {"description": "Not found"},
            }
        )

        app.p_q = self.p_q
        app.db = Repo()

        app.mount("/ui/", StaticFiles(directory="./webapp/static/ui", html=True), name="ui")

        app.include_router(security.router)
        app.include_router(admin.router)
        app.include_router(chat.router)
        app.include_router(custom.router)
        app.include_router(pet.router)
        app.include_router(mod.router)

        uvicorn.run(app, host="127.0.0.1", port=8080, log_level="info")
