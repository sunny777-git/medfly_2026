# app/routers/users.py

import os
from fastapi import APIRouter, Depends, HTTPException
import jwt
from sqlalchemy.orm import Session
from app.models.database import SessionLocal
from app.models.all_models import User
from app.schemas.all import UserLogin, UserRegister
from app.utils.security import hash_password, verify_password, create_access_token
from app.utils.deps import get_db, system_admin_required
from jose import jwt, JWTError

router = APIRouter()



@router.post("/login")
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.mobile == payload.mobile).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(payload.password, user.show_pwd):
        raise HTTPException(status_code=400, detail="Incorrect password")

    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}


@router.post("/register")
def register_user(payload: UserRegister, db: Session = Depends(get_db)):
    # Check if mobile already exists
    existing_user = db.query(User).filter(User.mobile == payload.mobile).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Mobile number already registered")

    # Create new user
    new_user = User(
        fullname=payload.fullname,
        mobile=payload.mobile,
        show_pwd=hash_password(payload.password),  # bcrypt hash
        is_active=True
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User registered successfully",
        "user_id": new_user.id
    }


def login_required(user: User = Depends(system_admin_required)) -> User:
    return user

@router.get("/user_profile")
def read_users_me(current_user: User = Depends(system_admin_required)):
    return {
        "id": current_user.id,
        "fullname": current_user.fullname,
        "mobile": current_user.mobile,
    }
