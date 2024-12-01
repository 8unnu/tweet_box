import random
import sys

import socketio

import uvicorn

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from loguru import logger

# logger.add(sink=sys.stdout, colorize=True, level="INFO")

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount('/static', StaticFiles(directory="static"))

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
socket_app = socketio.ASGIApp(sio, app)

users = {
    "jack": "000a"
}
@sio.event
async def connect(sid, env):
    logger.info(f"Client: {sid} has connect")

@sio.on("message")
async def message(sid, data):
    await sio.emit('message', [data['username'], data['message']], skip_sid=sid)
    logger.info(f"{sid}({data['username']}) say {data['message']}")

@sio.event
async def disconnect(sid):
    logger.info(f"Client: {sid} has disconnect")

@app.get("/")
async def index(request: Request):
    headers = request.headers.get("Authorization")
    context = {
        "request": request
    }
    return templates.TemplateResponse("index.html", context=context)

if __name__ == "__main__":
    uvicorn.run(socket_app, host="127.0.0.1", port=8000)
