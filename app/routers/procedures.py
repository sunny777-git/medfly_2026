from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from app.models import all_models as models
from app.schemas import all as schemas
from app.models.database import get_db

router = APIRouter()


@router.get("/procedures/", response_model=list[schemas.Procedure])
def get_procedures(
    hospid: int = Query(None),
    procedureid: int = Query(None),
    db: Session = Depends(get_db)
):
    if hospid and procedureid:
        return db.query(models.Procedure).filter_by(hospital_id=hospid, id=procedureid).all()
    elif hospid:
        return db.query(models.Procedure).filter_by(hospital_id=hospid).all()
    return db.query(models.Procedure).all()

@router.post("/procedures/", response_model=schemas.Procedure)
def create_procedure(procedure: schemas.ProcedureCreate, db: Session = Depends(get_db)):
    new_proc = models.Procedure(**procedure.dict())
    db.add(new_proc)
    db.commit()
    db.refresh(new_proc)
    return new_proc

@router.delete("/procedures/{id}")
def delete_procedure(id: int, db: Session = Depends(get_db)):
    db.query(models.Procedure).filter_by(id=id).delete()
    db.commit()
    return {"message": "Procedure deleted"}
