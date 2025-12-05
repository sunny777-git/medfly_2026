# app/routers/webrtc_signaling.py

import socketio
from fastapi import APIRouter

sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
router = APIRouter()

@sio.event
async def connect(sid, environ):
    print(f"🟢 Client connected: {sid}")

@sio.event
async def disconnect(sid):
    print(f"🔴 Client disconnected: {sid}")

@sio.event
async def join(sid, data):
    room = data.get("room")
    await sio.enter_room(sid, room)
    print(f"👥 {sid} joined room {room}")

@sio.event
async def offer(sid, data):
    to = data["to"]
    offer = data["offer"]
    await sio.emit("offer", {"from": sid, "offer": offer}, to=to)

@sio.event
async def answer(sid, data):
    to = data["to"]
    answer = data["answer"]
    await sio.emit("answer", {"from": sid, "answer": answer}, to=to)

@sio.event
async def candidate(sid, data):
    to = data["to"]
    candidate = data["candidate"]
    await sio.emit("candidate", {"from": sid, "candidate": candidate}, to=to)

@sio.event
async def viewer_ready(sid, data):
    viewer_id = sid  # use sid of the viewer who just connected
    room = data.get("room")
    # Notify broadcaster(s) in the same room that a viewer is ready
    await sio.emit("viewer-ready", {"viewer_id": viewer_id}, room=room)
    print(f"👀 Viewer {viewer_id} is ready in room {room}")
