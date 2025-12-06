# app/routers/hospitals.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.models.all_models import Hospital, User
from app.utils.deps import get_db, system_admin_required
from app.schemas.all import HospitalCreate, HospitalResponse
from app.utils.security import hash_password

router = APIRouter()


# GET all hospitals
@router.get("/", response_model=List[HospitalResponse])
def list_hospitals(
    db: Session = Depends(get_db),
    current_user: User = Depends(system_admin_required),
):
    return db.query(Hospital).all()


# POST a new hospital  ✅ also auto-creates a login user
@router.post("/create_hospital", response_model=HospitalResponse)
def create_hospital(
    hospital: HospitalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(system_admin_required),
):
    # 1) create Hospital record
    db_hospital = Hospital(**hospital.dict())
    db.add(db_hospital)
    db.flush()  # get db_hospital.id before commit

    # 2) generate login_name for this hospital admin
    #    example: prefix="APLH", id=2 -> "APLH002"
    prefix = hospital.prefix or "MEDF"
    login_name = f"{prefix}{db_hospital.id:03d}"

    # 3) default common password
    default_password = "Medfly2025"

    # ensure login_name unique
    existing_login = db.query(User).filter(User.login_name == login_name).first()
    if existing_login:
        raise HTTPException(
            status_code=400,
            detail=f"Login name {login_name} already exists",
        )

    # ensure mobile unique (as before)
    if hospital.mobile:
        existing_mobile = db.query(User).filter(User.mobile == hospital.mobile).first()
        if existing_mobile:
            raise HTTPException(
                status_code=400,
                detail=f"Mobile {hospital.mobile} already registered as a user",
            )

    # 4) create hospital admin user
    new_user = User(
        fullname=hospital.owner_name or hospital.name,
        mobile=hospital.mobile,
        login_name=login_name,                          # ✅ login ID like APLH002
        role_name="hospital_admin",
        is_sadmin=False,
        is_hadmin=True,
        hspId=str(db_hospital.id),
        show_pwd=hash_password(default_password),
        is_active=True,
    )
    db.add(new_user)

    # 5) commit everything
    db.commit()
    db.refresh(db_hospital)

    return db_hospital


# GET hospital by ID
@router.get("/{hospital_id}", response_model=HospitalResponse)
def get_hospital(
    hospital_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(system_admin_required),
):
    hospital = db.query(Hospital).filter(Hospital.id == hospital_id).first()
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found")
    return hospital



