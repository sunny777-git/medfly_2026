from datetime import datetime
from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from app.schemas.all import PatientRegistration, PatientInfo
from app.models import all_models as models
from app.models.database import get_db

router = APIRouter()

@router.post("/summary-dates-filter")
def business_dates_filter(
    hospid: int = Query(...),
    from_date: str = Query(...),
    to_date: str = Query(...),
    selected_procedure: Optional[str] = Query(None),
    selected_referrer: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(models.PatientRegistration).filter(
        models.PatientRegistration.hospital_id == hospid,
        models.PatientRegistration.entry_date >= from_date,
        models.PatientRegistration.entry_date <= to_date
    )

    if selected_procedure:
        query = query.filter(models.PatientRegistration.procedure_name == selected_procedure)
    if selected_referrer:
        query = query.filter(models.PatientRegistration.referrer_name == selected_referrer)

    pr_data = query.all()
    result = []

    for pr in pr_data:
        pat = db.query(models.PatientInfo).filter_by(mf_id=pr.mf_id).first()
        if pat:
            result.append({
                "Mf_Id": pat.mf_id,
                "Patient_Name": pat.name,
                "Alt_Id": pat.alt_id,
                "Mobile": pat.mobile,
                "Entry_Date": pr.entry_date,
                "Referrer_Name": pr.referrer_name,
                "Procedure_Name": pr.procedure_name
            })

    return result


@router.get("/user-based-data/")
def get_user_based_data(
    hospid: int = Query(...),
    user_id: str = Query(...),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    # Initial query
    query = db.query(models.PatientRegistration).filter(
        models.PatientRegistration.hospital_id == hospid,
        models.PatientRegistration.doctor_id == user_id
    )

    # Optional date filtering
    if from_date and to_date:
        try:
            from_dt = datetime.strptime(from_date, "%Y-%m-%d").date()
            to_dt = datetime.strptime(to_date, "%Y-%m-%d").date()
            query = query.filter(
                models.PatientRegistration.entry_date >= from_dt,
                models.PatientRegistration.entry_date <= to_dt
            )
        except ValueError:
            return JSONResponse(
                {"error": "Invalid date format. Use YYYY-MM-DD."},
                status_code=400
            )

    # Pagination
    total_count = query.count()
    registrations = query.offset((page - 1) * page_size).limit(page_size).all()

    patientinfo_data = []
    patientreg_data = []

    for reg in registrations:
        pinfo = db.query(models.PatientInfo).filter_by(
            hospital_id=hospid,
            mf_id=reg.mf_id
        ).first()
        if pinfo:
            patientinfo_data.append({
                "Mf_Id": pinfo.mf_id,
                "Patient_Name": pinfo.name,
                "Mobile": pinfo.mobile
            })

        patientreg_data.append({
            "Mf_Id": reg.mf_id,
            "Alt_Id": reg.alt_id,
            "Reg_Date": reg.entry_date,
            "Referrer_Name": reg.referrer_name,
            "Procedure_Name": reg.procedure_name
        })

    return {
        "page": page,
        "page_size": page_size,
        "total": total_count,
        "patientinfoData": patientinfo_data,
        "patientregData": patientreg_data
    }




