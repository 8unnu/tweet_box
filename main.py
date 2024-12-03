import random

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

rooms_numbers = []
free_rooms_numbers = []
rooms = {}

@sio.event
async def connect(sid, env):
    if len(free_rooms_numbers) != 0:
        room_number = free_rooms_numbers[random.randint(0, len(free_rooms_numbers) - 1)]
        free_rooms_numbers.remove(room_number)
        room = f"room_{room_number}"

        await sio.enter_room(sid, room=room)
        rooms[room].append(sid)

        await sio.emit("message", ["system", f"Your opponent has joined"], room=room, skip_sid=sid)
        await sio.emit("message", ["system", f"You joined your opponent"], room=room, skip_sid=rooms[room][0])

        logger.info(f"Client: {sid} has connect {room} to {rooms[room][0]}")
    else:
        room_number = 1
        while room_number in rooms_numbers:
            room_number = random.randint(1, 999)
        room = f"room_{room_number}"

        await sio.enter_room(sid, room=room)
        rooms_numbers.append(room_number)
        free_rooms_numbers.append(room_number)
        rooms[room] = [sid]

        await sio.emit("message", ["system", f"You've join {room}. Expect an opponent."], room=room)

        logger.info(f"Client: {sid} has connect {room} and wait your opponent")


@sio.on("message")
async def message(sid, data):
    user_room = [i for i in sio.rooms(sid) if i != sid][0]
    await sio.emit('message', [data['username'], data['message']], room=user_room, skip_sid=sid)
    logger.info(f"{sid}({data['username']}) say {data['message']}")

@sio.event
async def disconnect(sid):
    user_rooms = sio.rooms(sid)
    user_room = [i for i in user_rooms if i != sid][0]

    await sio.emit("message", ["system", "Your opponent is out, the room is closed"], room=user_room)

    for id in rooms[user_room]:
        await sio.disconnect(id)
    await sio.close_room(user_room)

    room_number = int(user_room.split("_")[1])
    if room_number in rooms_numbers:
        rooms_numbers.remove(room_number)
    try:
        rooms.pop(user_room)
    except KeyError:
        pass
    logger.info(f"room_{room_number} delete and users has disconnect")

@app.get("/")
async def index(request: Request):
    context = {
        "request": request
    }
    return templates.TemplateResponse("index.html", context=context)

if __name__ == "__main__":
    uvicorn.run(socket_app, host="127.0.0.1", port=8000)