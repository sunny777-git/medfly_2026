# app/utils/deps.py

import os
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import jwt, JWTError

from app.models.database import SessionLocal
from app.models.all_models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/users/login")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(status_code=401, detail="Invalid token")

    try:
        payload = jwt.decode(
            token,
            os.getenv("SECRET_KEY"),
            algorithms=[os.getenv("ALGORITHM")],
        )
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == int(user_id)).first()
    finally:
        db.close()

    if user is None:
        raise credentials_exception

    return user


def system_admin_required(user: User = Depends(get_current_user)) -> User:
    if not user.is_sadmin:
        raise HTTPException(status_code=403, detail="System admin access only")
    return user


# ✅ NEW: allow both system admin OR hospital admin
def hospital_or_system_admin_required(user: User = Depends(get_current_user)) -> User:
    if not (user.is_sadmin or user.is_hadmin):
        raise HTTPException(
            status_code=403,
            detail="Hospital or system admin access only",
        )
    return user
