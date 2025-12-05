from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from app.models import all_models as models
from app.schemas import all as schemas
from app.models.database import get_db

router = APIRouter()


@router.get("/roles/", response_model=list[schemas.Role])
def get_roles(
    hospid: int = Query(None),
    roleid: int = Query(None),
    db: Session = Depends(get_db)
):
    if hospid and roleid:
        return db.query(models.Role).filter_by(hospital_id=hospid, id=roleid).all()
    elif hospid:
        base_roles = db.query(models.Role).filter_by(id=2).all()
        hosp_roles = db.query(models.Role).filter_by(hospital_id=hospid).all()
        return list(set(hosp_roles + base_roles))
    return db.query(models.Role).filter_by(id=2).all()

@router.post("/roles/", response_model=schemas.Role)
def create_role(role: schemas.RoleCreate, db: Session = Depends(get_db)):
    new_role = models.Role(**role.dict())
    db.add(new_role)
    db.commit()
    db.refresh(new_role)
    return new_role

@router.put("/roles/{id}", response_model=schemas.Role)
def update_role(id: int, role: schemas.RoleCreate, db: Session = Depends(get_db)):
    db_role = db.query(models.Role).filter_by(id=id).first()
    if not db_role:
        raise HTTPException(status_code=404, detail="Role not found")
    for key, value in role.dict().items():
        setattr(db_role, key, value)
    db.commit()
    return db_role

@router.delete("/roles/{id}")
def delete_role(id: int, db: Session = Depends(get_db)):
    db.query(models.Role).filter_by(id=id).delete()
    db.commit()
    return {"message": "Role deleted"}


