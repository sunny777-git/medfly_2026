from typing import List, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.models.all_models import Hospital
from app.schemas.all import HospitalResponse
from app.utils.deps import get_db, system_admin_required

router = APIRouter(
    tags=["dashboard"],
    dependencies=[Depends(system_admin_required)],
)


@router.get("/hospitals")
def hospitals_dynamic(
    hospital_id: Optional[int] = Query(
        None,
        description="If omitted: returns all main/independent hospitals. "
                    "If provided: works in branch mode.",
    ),
    branch_id: Optional[int] = Query(
        None,
        description="Optional branch ID. Valid only when hospital_id is provided.",
    ),
    db: Session = Depends(get_db),
):
    """
    One fully dynamic API:

    1) GET /api/dashboard/hospitals
       -> returns list[HospitalResponse]
          All main/independent hospitals (parent_id IS NULL)

    2) GET /api/dashboard/hospitals?hospital_id=1
       -> returns list[HospitalResponse]
          All branches for hospital_id = 1

    3) GET /api/dashboard/hospitals?hospital_id=1&branch_id=2
       -> returns HospitalResponse
          Only that specific branch under that hospital
    """

    # --- CASE 1: no hospital_id -> list all main/independent hospitals ---
    if hospital_id is None:
        hospital_objs = (
            db.query(Hospital)
            .filter(Hospital.parent_id.is_(None))  # parent_id = NULL
            .all()
        )

        return [
            HospitalResponse.model_validate(h, from_attributes=True)
            for h in hospital_objs
        ]

    # From here: hospital_id is provided
    hospital_obj = db.query(Hospital).filter(Hospital.id == hospital_id).first()
    if not hospital_obj:
        raise HTTPException(status_code=404, detail="Hospital not found")

    # --- CASE 3: hospital_id + branch_id -> specific branch ONLY ---
    if branch_id is not None:
        branch_obj = (
            db.query(Hospital)
            .filter(
                Hospital.id == branch_id,
                Hospital.parent_id == hospital_id,  # ensure it belongs to this hospital
            )
            .first()
        )

        if not branch_obj:
            raise HTTPException(
                status_code=404,
                detail="Branch not found for this hospital",
            )

        return HospitalResponse.model_validate(branch_obj, from_attributes=True)

    # --- CASE 2: hospital_id only -> ALL branches of that hospital ---
    branch_objs = (
        db.query(Hospital)
        .filter(Hospital.parent_id == hospital_id)
        .all()
    )

    return [
        HospitalResponse.model_validate(b, from_attributes=True)
        for b in branch_objs
    ]
