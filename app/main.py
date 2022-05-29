from fastapi import FastAPI
from fastapi import FastAPI, Request
import routers as router

from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get('/')
async def Home():
    return 'Welcome Home'


app.include_router(router.router)
