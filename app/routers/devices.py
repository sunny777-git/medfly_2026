from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional, List

from app.models.all_models import Device as DeviceModel
from app.schemas.all import Device, DeviceCreate, DeviceListResponse
from app.models.database import get_db

router = APIRouter()

@router.get("/", response_model=List[Device])
def get_devices(
    hospid: Optional[int] = Query(None),
    deviceid: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(DeviceModel)
    if hospid:
        query = query.filter(DeviceModel.hospital_id == hospid)
    if deviceid:
        query = query.filter(DeviceModel.id == deviceid)
    return query.all()

@router.post("/", response_model=Device, status_code=status.HTTP_201_CREATED)
def create_device(device: DeviceCreate, db: Session = Depends(get_db)):
    new_device = DeviceModel(**device.dict())
    db.add(new_device)
    db.commit()
    db.refresh(new_device)
    return new_device

@router.put("/", response_model=Device)
def update_device(device: Device, db: Session = Depends(get_db)):
    existing_device = db.query(DeviceModel).filter(DeviceModel.id == device.id).first()
    if not existing_device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    for field, value in device.dict(exclude_unset=True).items():
        setattr(existing_device, field, value)

    db.commit()
    db.refresh(existing_device)
    return existing_device

@router.delete("/", status_code=status.HTTP_200_OK)
def delete_device(deviceid: int = Query(...), db: Session = Depends(get_db)):
    device = db.query(DeviceModel).filter(DeviceModel.id == deviceid).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    db.delete(device)
    db.commit()
    return {"detail": f"Device with id {deviceid} deleted successfully"}


@router.get("/", response_model=DeviceListResponse)
def get_devices(
    hospid: Optional[int] = Query(None),
    deviceid: Optional[int] = Query(None),
    device_uid: Optional[str] = Query(None),
    is_default: Optional[bool] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    query = db.query(DeviceModel)

    # Filtering
    if hospid:
        query = query.filter(DeviceModel.hospital_id == hospid)
    if deviceid:
        query = query.filter(DeviceModel.id == deviceid)
    if device_uid:
        query = query.filter(DeviceModel.device_id == device_uid)
    if is_default is not None:
        query = query.filter(DeviceModel.is_default == is_default)

    total = query.count()
    devices = query.offset(offset).limit(limit).all()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "devices": devices
    }