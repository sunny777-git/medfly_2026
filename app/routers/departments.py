from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from app.models import all_models as models
from app.schemas import all as schemas
from app.models.database import get_db

router = APIRouter()

@router.get("/departments/", response_model=list[schemas.Department])
def get_departments(
    hospid: int = Query(None),
    departmentid: int = Query(None),
    db: Session = Depends(get_db)
):
    if hospid and departmentid:
        return db.query(models.Department).filter_by(hospital_id=hospid, id=departmentid).all()
    elif hospid:
        return db.query(models.Department).filter_by(hospital_id=hospid).all()
    return db.query(models.Department).all()

@router.post("/departments/", response_model=schemas.Department)
def create_department(dept: schemas.DepartmentCreate, db: Session = Depends(get_db)):
    new_dept = models.Department(**dept.dict())
    db.add(new_dept)
    db.commit()
    db.refresh(new_dept)
    return new_dept

@router.put("/departments/{id}", response_model=schemas.Department)
def update_department(id: int, dept: schemas.DepartmentCreate, db: Session = Depends(get_db)):
    department = db.query(models.Department).filter_by(id=id).first()
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")
    for key, value in dept.dict().items():
        setattr(department, key, value)
    db.commit()
    return department

@router.delete("/departments/{id}")
def delete_department(id: int, db: Session = Depends(get_db)):
    db.query(models.Department).filter_by(id=id).delete()
    db.commit()
    return {"message": "Department deleted"}
