from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.database import get_db
from app.models import all_models as models
from app.schemas import all as schemas
from app.utils.deps import hospital_or_system_admin_required
from app.models.all_models import User  # or use models.User below

router = APIRouter()


@router.get(
    "/patient-registration/",
    response_model=schemas.PaginatedResponse[schemas.PatientRegistration],
)
def get_patient_registrations(
    hospid: Optional[int] = Query(None),
    mfid: Optional[str] = Query(None),
    limit: int = Query(50, gt=0, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(models.PatientRegistration)
    if hospid:
        query = query.filter(models.PatientRegistration.hospital_id == hospid)
    if mfid:
        query = query.filter(models.PatientRegistration.mf_id == mfid)

    total = query.count()
    results = query.offset(offset).limit(limit).all()

    return schemas.PaginatedResponse(
        total=total,
        limit=limit,
        offset=offset,
        items=results,
    )


@router.post("/patient-registration/", response_model=schemas.PatientRegistration)
def create_patient_registration(
    registration: schemas.PatientRegistrationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(hospital_or_system_admin_required),
):
    # Always tie registration to the current user's branch
    if not current_user.hspId:
        raise HTTPException(
            status_code=400,
            detail="User is not linked to any hospital/branch",
        )

    data = registration.dict()

    # 🔁 FIX: map 'date' (schema) -> 'procedure_date' (DB column)
    date_value = data.pop("date", None)
    if date_value:
        data["procedure_date"] = date_value

    data["hospital_id"] = int(current_user.hspId)  # branch id

    new_entry = models.PatientRegistration(**data)
    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)
    return new_entry


@router.put("/patient-registration/{id}", response_model=schemas.PatientRegistration)
def update_patient_registration(
    id: int,
    update_data: schemas.PatientRegistrationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(hospital_or_system_admin_required),
):
    reg = db.query(models.PatientRegistration).filter_by(id=id).first()
    if not reg:
        raise HTTPException(status_code=404, detail="Patient Registration not found")

    data = update_data.dict()

    # 🔁 FIX: same mapping for update
    date_value = data.pop("date", None)
    if date_value:
        data["procedure_date"] = date_value

    # Optionally, you can enforce hospital_id stays same and ignore if present in schema
    # data.pop("hospital_id", None)

    for key, value in data.items():
        setattr(reg, key, value)

    db.commit()
    db.refresh(reg)
    return reg


@router.delete("/patient-registration/{id}")
def delete_patient_registration(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(hospital_or_system_admin_required),
):
    deleted = db.query(models.PatientRegistration).filter_by(id=id).delete()
    db.commit()
    return {"message": "Patient registration deleted", "id": id}


@router.get("/search-patients/")
def search_patients(
    hospid: int = Query(...),
    db: Session = Depends(get_db),
):
    mf_ids = (
        db.query(models.PatientInfo.mf_id)
        .filter(models.PatientInfo.hospital_id == hospid)
        .all()
    )
    mf_ids = [mfid for (mfid,) in mf_ids]  # unpack tuple

    results = []
    for mfid in mf_ids:
        pinfo = (
            db.query(models.PatientInfo)
            .filter(models.PatientInfo.mf_id == mfid)
            .first()
        )
        preg = (
            db.query(models.PatientRegistration)
            .filter(models.PatientRegistration.mf_id == mfid)
            .first()
        )
        if pinfo and preg:
            results.append(
                {
                    "Patient_Name": pinfo.name,
                    "Mobile": pinfo.mobile,
                    "Alt_Id": pinfo.alt_id,
                    "Date": pinfo.registered_on,
                    "Procedure_Name": preg.procedure_name,
                    "Doctor_Name": preg.doctor_name,
                    "Referrer_Name": preg.referrer_name,
                    "Mf_Id": preg.mf_id,
                }
            )
    return JSONResponse(content={"patientslist": results})


@router.get(
    "/patients/",
    response_model=schemas.PaginatedResponse[schemas.PatientInfo],
)
def get_patients(
    hospid: Optional[int] = Query(None),
    limit: int = Query(50, gt=0),
    offset: int = Query(0),
    db: Session = Depends(get_db),
):
    query = db.query(models.PatientInfo)
    if hospid:
        query = query.filter(models.PatientInfo.hospital_id == hospid)

    total = query.count()
    items = query.offset(offset).limit(limit).all()
    return schemas.PaginatedResponse(
        total=total,
        limit=limit,
        offset=offset,
        items=items,
    )
