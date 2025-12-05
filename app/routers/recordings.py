# app/routers/recordings.py

from typing import List
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
import shutil
import os

router = APIRouter()

UPLOAD_DIR = "app/uploads/recordings"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/save-recording")
async def save_recording(video: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, video.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(video.file, buffer)
    return {"message": "Recording saved", "filename": video.filename}


@router.get("/recordings", response_model=List[str])
async def list_recordings():
    files = [f for f in os.listdir(UPLOAD_DIR) if f.endswith(".webm")]
    return files


@router.get("/recordings/{filename}")
async def get_recording(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="video/webm")
    return JSONResponse(status_code=404, content={"detail": "File not found"})


@router.delete("/recordings/{filename}")
def delete_recording(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Recording not found")

    os.remove(file_path)
    return {"message": "Recording deleted"}