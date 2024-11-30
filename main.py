import socketio
import uvicorn
from fastapi import FastAPI

app = FastAPI()
sio = socketio.AsyncServer(async_mode="asgi")
socket_app = socketio.ASGIApp(sio, app)

@sio.event
async def connect(sid, env):
    print(f"Client: {sid} has connect")

@sio.event
async def disconnect(sid):
    print(f"Client: {sid} has disconnect")

if __name__ == "__main__":
    uvicorn.run(socket_app)