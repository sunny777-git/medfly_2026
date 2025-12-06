from datetime import date
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.models.database import get_db
from app.models import all_models as models
from app.schemas import all as schemas
from app.utils.deps import hospital_or_system_admin_required
from app.models.all_models import User

router = APIRouter()


# ============================================================
# 1️⃣ PATIENT-REGISTRATION APIs
# ============================================================

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
    # Ensure hospital_id exists on user
    if not current_user.hspId:
        raise HTTPException(status_code=400, detail="User is not linked to any hospital/branch")

    data = registration.dict()
    hospital_id = int(current_user.hspId)

    # -----------------------------------------------
    # 1️⃣ Map date -> procedure_date
    # -----------------------------------------------
    date_value = data.pop("date", None)
    if date_value:
        data["procedure_date"] = date_value

    data["hospital_id"] = hospital_id

    # -----------------------------------------------
    # 2️⃣ Extract patient fields for patient_info
    # -----------------------------------------------
    mf_id = data.get("mf_id")
    if not mf_id:
        raise HTTPException(status_code=400, detail="mf_id is required")

    alt_id = data.get("alt_id") or "--"
    name = data.get("name")            # patient name from frontend
    mobile = data.get("mobile")
    age = data.get("age")
    gender = data.get("gender")

    # -----------------------------------------------
    # 3️⃣ UPSERT PatientInfo
    # -----------------------------------------------
    pinfo = (
        db.query(models.PatientInfo)
        .filter(
            models.PatientInfo.mf_id == mf_id,
            models.PatientInfo.hospital_id == hospital_id,
        )
        .first()
    )

    if pinfo:
        # Update fields if provided
        if name:
            pinfo.name = name
        if mobile:
            pinfo.mobile = mobile
        if age is not None:
            pinfo.age = age
        if gender:
            pinfo.gender = gender
        if alt_id and alt_id != "--":
            pinfo.alt_id = alt_id

        # Increment total visits
        pinfo.total_visits = (pinfo.total_visits or 0) + 1

        # If registered_on was empty, set it once
        if not pinfo.registered_on:
            pinfo.registered_on = data.get("procedure_date") or date.today().isoformat()

    else:
        # Create new patient record
        registered_on = data.get("procedure_date") or date.today().isoformat()

        pinfo = models.PatientInfo(
            hospital_id=hospital_id,
            mf_id=mf_id,
            alt_id=alt_id,
            name=name or "",
            mobile=mobile or "",
            age=age if age is not None else None,
            gender=gender or "",
            registered_on=registered_on,
            total_visits=1,
        )
        db.add(pinfo)

    # 🔹 Decide visit number (after total_visits is correct)
    visit_number = pinfo.total_visits or 1

    # -----------------------------------------------
    # 4️⃣ Remove patient-only fields from registration payload
    # -----------------------------------------------
    for field in ["name", "mobile", "age", "gender"]:
        data.pop(field, None)

    # Set visit_id explicitly based on total_visits
    data["visit_id"] = visit_number

    # -----------------------------------------------
    # 5️⃣ Create PatientRegistration entry
    # -----------------------------------------------
    new_entry = models.PatientRegistration(**data)
    db.add(new_entry)

    # Single commit for both tables
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

    # map 'date' (schema) -> 'procedure_date'
    date_value = data.pop("date", None)
    if date_value:
        data["procedure_date"] = date_value

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



# ============================================================
# 2️⃣ FIND-PATIENTS API
# ============================================================

@router.get("/find-patients/")
def find_patients(
    mfid: Optional[str] = Query(None),
    alt_id: Optional[str] = Query(None),
    patient_name: Optional[str] = Query(None),
    doctor_name: Optional[str] = Query(None),
    procedure_name: Optional[str] = Query(None),
    hospid: Optional[int] = Query(None),
    limit: int = Query(50, gt=0, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(hospital_or_system_admin_required),
):
    """
    Unified flexible search combining:
    - mfid
    - alt_id
    - patient_name (PatientInfo)
    - doctor_name
    - procedure_name
    """

    query = (
        db.query(models.PatientRegistration, models.PatientInfo)
        .join(
            models.PatientInfo,
            models.PatientInfo.mf_id == models.PatientRegistration.mf_id,
            isouter=True,
        )
    )

    # Hospital restrictions
    if not current_user.is_sadmin:
        query = query.filter(
            models.PatientRegistration.hospital_id == int(current_user.hspId)
        )
    elif hospid:
        query = query.filter(models.PatientRegistration.hospital_id == hospid)

    # Filters
    if mfid:
        query = query.filter(models.PatientRegistration.mf_id == mfid)

    if alt_id:
        query = query.filter(models.PatientRegistration.alt_id == alt_id)

    if patient_name:
        query = query.filter(models.PatientInfo.name.ilike(f"%{patient_name}%"))

    if doctor_name:
        query = query.filter(models.PatientRegistration.doctor_name.ilike(f"%{doctor_name}%"))

    if procedure_name:
        query = query.filter(models.PatientRegistration.procedure_name.ilike(f"%{procedure_name}%"))

    total = query.count()

    rows = (
        query.order_by(models.PatientRegistration.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    results = []
    for reg, pinfo in rows:
        results.append(
            {
                "Registration_Id": reg.id,
                "Hospital_Id": reg.hospital_id,
                "Mf_Id": reg.mf_id,
                "Alt_Id": reg.alt_id,
                "Status": reg.status,
                "Procedure_Name": reg.procedure_name,
                "Doctor_Name": reg.doctor_name,
                "Referrer_Name": reg.referrer_name,
                "Nurse_Name": reg.nurse_name,
                "Procedure_Date": reg.procedure_date,
                "Entry_Date": reg.entry_date,
                # From PatientInfo
                "Patient_Name": pinfo.name if pinfo else None,
                "Mobile": pinfo.mobile if pinfo else None,
                "Age": pinfo.age if pinfo else None,
                "Gender": pinfo.gender if pinfo else None,
                "Registered_On": pinfo.registered_on if pinfo else None,
                "Total_Visits": pinfo.total_visits if pinfo else None,
            }
        )

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": results,
    }


# ============================================================
# 3️⃣ PATIENT VISITS API
#     One patient (by mfid) → master info + all visits
# ============================================================

@router.get("/patient-visits/{mfid}")
def get_patient_visits(
    mfid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(hospital_or_system_admin_required),
):
    """
    Returns:
    - patient: master info (from PatientInfo)
    - visits_count: number of visits (registrations)
    - visits: list of visit records (from PatientRegistration)
    """

    # 1️⃣ Patient master
    pinfo_query = db.query(models.PatientInfo).filter(models.PatientInfo.mf_id == mfid)

    if not current_user.is_sadmin:
        pinfo_query = pinfo_query.filter(
            models.PatientInfo.hospital_id == int(current_user.hspId)
        )

    pinfo = pinfo_query.first()
    if not pinfo:
        raise HTTPException(status_code=404, detail="Patient not found for this MF ID")

    # 2️⃣ All registrations (visits)
    regs_query = db.query(models.PatientRegistration).filter(
        models.PatientRegistration.mf_id == mfid
    )

    if not current_user.is_sadmin:
        regs_query = regs_query.filter(
            models.PatientRegistration.hospital_id == int(current_user.hspId)
        )

    regs = (
        regs_query
        .order_by(models.PatientRegistration.visit_id.desc(),
                  models.PatientRegistration.id.desc())
        .all()
    )

    visits_count = len(regs)

    visits = []
    for reg in regs:
        visits.append(
            {
                "Visit_Id": reg.visit_id,
                "Registration_Id": reg.id,
                "Hospital_Id": reg.hospital_id,
                "Status": reg.status,
                "Procedure_Name": reg.procedure_name,
                "Doctor_Name": reg.doctor_name,
                "Referrer_Name": reg.referrer_name,
                "Nurse_Name": reg.nurse_name,
                "Procedure_Date": reg.procedure_date,
                "Entry_Date": reg.entry_date,
            }
        )

    patient_obj = {
        "Hospital_Id": pinfo.hospital_id,
        "Mf_Id": pinfo.mf_id,
        "Alt_Id": pinfo.alt_id,
        "Name": pinfo.name,
        "Mobile": pinfo.mobile,
        "Age": pinfo.age,
        "Gender": pinfo.gender,
        "Registered_On": pinfo.registered_on,
        "Total_Visits": pinfo.total_visits,
    }

    return {
        "patient": patient_obj,
        "visits_count": visits_count,
        "visits": visits,
    }
