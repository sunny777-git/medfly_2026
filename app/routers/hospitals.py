# app/routers/hospitals.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.all_models import Hospital, User 

from app.utils.deps import get_db, system_admin_required

from app.schemas.all import HospitalCreate, HospitalResponse
from typing import List

router = APIRouter()

# GET all hospitals
@router.get("/", response_model=List[HospitalResponse])
def list_hospitals(db: Session = Depends(get_db), current_user: User = Depends(system_admin_required)):
    return db.query(Hospital).all()

# POST a new hospital
@router.post("/create_hospital", response_model=HospitalResponse)
def create_hospital(hospital: HospitalCreate, db: Session = Depends(get_db), current_user: User = Depends(system_admin_required)):
    db_hospital = Hospital(**hospital.dict())
    db.add(db_hospital)
    db.commit()
    db.refresh(db_hospital)
    return db_hospital

# GET hospital by ID
@router.get("/{hospital_id}", response_model=HospitalResponse)
def get_hospital(hospital_id: int, db: Session = Depends(get_db), current_user: User = Depends(system_admin_required)):
    hospital = db.query(Hospital).filter(Hospital.id == hospital_id).first()
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found")
    return hospital
