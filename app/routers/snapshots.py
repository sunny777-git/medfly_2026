# app/routers/snapshots.py

import base64
import os
import time
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Query, UploadFile, Depends, HTTPException, status, Body, File
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.models import all_models as models
from app.schemas import all as schemas
from app.models.database import get_db
from dotenv import load_dotenv
load_dotenv()

router = APIRouter()


# POST /api/save-snapshots/ (base64 JSON upload)
@router.post("/save-snapshots/", response_model=schemas.Snapshots)
def upload_snapshot_base64(
    payload: dict = Body(...),
    db: Session = Depends(get_db)
):
    try:
        hospital_id = payload.get("hospital_id")
        uid = payload.get("uid")
        visit_id = payload.get("visit_id")
        procedure_id = payload.get("procedure_id", 0)
        procedure_datetime = payload.get("procedure_datetime") or datetime.utcnow().isoformat()

        file_type = payload.get("file_type", "image/png")
        file_status = payload.get("file_status", "main")
        annotation_data = payload.get("annotation_data", "")
        filename = payload.get("filename", f"snapshot_{int(time.time())}.png")
        base64_image = payload.get("Img")

        if not base64_image:
            raise ValueError("Missing image data")

        _, imgstr = base64_image.split(';base64,') if ';base64,' in base64_image else ('', base64_image)
        img_data = base64.b64decode(imgstr)

        file_src = f"/uploads/snapshots/{filename}"
        abs_save_path = os.path.join(os.getenv("UPLOAD_DIR"),"snapshots", filename)
        os.makedirs(os.path.dirname(abs_save_path), exist_ok=True)

        with open(abs_save_path, "wb") as f:
            f.write(img_data)

        new_snapshot = models.Snapshots(
            hospital_id=hospital_id,
            uid=uid,
            visit_id=visit_id,
            procedure_id=procedure_id,
            procedure_datetime=procedure_datetime,
            file_src=file_src,
            file_thumbnail=file_src,  # optional: set to same or blank
            file_type=file_type,
            file_status=file_status,
            annotation_data=annotation_data
        )
        db.add(new_snapshot)
        db.commit()
        db.refresh(new_snapshot)

        return new_snapshot


    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Snapshot upload failed: {str(e)}")

# GET snapshots
@router.get("/snapshots/", response_model=dict)
def get_snapshots(
    hospid: Optional[int] = Query(None),
    mfid: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(models.Snapshots)
    if hospid:
        query = query.filter(models.Snapshots.hospital_id == hospid)
    if mfid:
        query = query.filter(models.Snapshots.uid == mfid)

    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    # ✅ serialize items safely
    return JSONResponse(content=jsonable_encoder({
        "page": page,
        "page_size": page_size,
        "total": total,
        "mediafiles": items
    }))

@router.delete("/snapshots/", response_model=dict)
def delete_snapshot(id: int = Query(...), db: Session = Depends(get_db)):
    snap = db.query(models.Snapshots).filter_by(id=id).first()
    if not snap:
        raise HTTPException(status_code=404, detail="Snapshot not found")

    if snap.file_src:
        # ✅ Remove leading slash and convert to absolute path relative to app dir
        rel_path = snap.file_src.lstrip("/")  # "uploads/snapshots/..."
        file_path = os.path.join("app", rel_path)

        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"🗑️ Deleted file: {file_path}")
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"File deletion error: {str(e)}")

    db.delete(snap)
    db.commit()
    return {"success": True, "deleted_id": id}