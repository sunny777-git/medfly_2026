# main.py (FastAPI replacement of Flask backend)
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from redis import Redis
from uuid import uuid4
import os, shutil, asyncio

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Redis queue setup
redis = Redis(host="localhost", port=6379, decode_responses=True)

# In-memory room tracking
rooms = {}

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    room = None
    user_id = str(uuid4())
    try:
        while True:
            data = await websocket.receive_json()
            if data['type'] == 'join':
                room = data['room']
                rooms.setdefault(room, {})[user_id] = websocket
                is_broadcaster = data.get('broadcaster', False)
                if not is_broadcaster:
                    # Notify broadcaster viewer is ready
                    for uid, ws in rooms[room].items():
                        if uid != user_id:
                            await ws.send_json({"type": "viewer-ready", "viewer_id": user_id})
            elif data['type'] in ('offer', 'answer', 'candidate'):
                to_id = data['to']
                if to_id in rooms[room]:
                    await rooms[room][to_id].send_json({**data, 'from': user_id})
    except WebSocketDisconnect:
        if room and user_id in rooms.get(room, {}):
            del rooms[room][user_id]

@app.post("/save-recording")
async def save_recording(video: UploadFile = File(...)):
    filename = f"{uuid4().hex}_{video.filename}"
    save_path = f"videos/{filename}"
    os.makedirs("videos", exist_ok=True)
    with open(save_path, "wb") as f:
        shutil.copyfileobj(video.file, f)

    redis.lpush("video_queue", filename)
    return {"filename": filename}

@app.get("/uploaded/{filename}")
async def uploaded(filename: str):
    path = f"https://your-supabase-cdn.com/recordings/{filename}"
    # In real scenario, check if uploaded to Supabase
    return {"url": path if filename.endswith(".webm") else ""}

@app.get("/ice-servers")
async def get_ice():
    return {
        "iceServers": [
            {"urls": "stun:stun.l.google.com:19302"},
            {
                "urls": "turn:115.98.148.169:3478",
                "username": "nani",
                "credential": "pass123"
            }
        ]
    }
