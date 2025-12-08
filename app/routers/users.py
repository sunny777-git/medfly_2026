# app/routers/users.py

import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from jose import jwt, JWTError

from app.models.database import SessionLocal
from app.models.all_models import User
from app.schemas.all import UserLogin, UserRegister
from app.utils.security import hash_password, verify_password, create_access_token
from app.utils.deps import get_db, system_admin_required

router = APIRouter()


@router.post("/login")
def login(payload: UserLogin, db: Session = Depends(get_db)):
    """
    Login using login_name + password.
    For hospital admins this will be the generated ID (e.g., APLH001).
    """

    user = db.query(User).filter(User.login_name == payload.login_name).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # ✅ Prefer hashed_password
    if user.hashed_password:
        if not verify_password(payload.password, user.hashed_password):
            raise HTTPException(status_code=400, detail="Incorrect password")
    else:
        # Optional: for old data where hash was incorrectly stored in show_pwd
        if not user.show_pwd or not verify_password(payload.password, user.show_pwd):
            raise HTTPException(status_code=400, detail="Incorrect password")

    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}



@router.post("/register")
def register_user(payload: UserRegister, db: Session = Depends(get_db)):
    """
    Public/normal user registration.
    - mobile is still required
    - login_name defaults to mobile (so they can log in with mobile as username)
    """

    # Check if mobile already exists
    existing_user = db.query(User).filter(User.mobile == payload.mobile).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Mobile number already registered")

    # Also ensure login_name (mobile) isn't already taken
    existing_login = db.query(User).filter(User.login_name == payload.mobile).first()
    if existing_login:
        raise HTTPException(status_code=400, detail="Login name already taken")

    plain_password = payload.password

    new_user = User(
        fullname=payload.fullname,
        mobile=payload.mobile,
        login_name=payload.login_name,                    # login with mobile
        show_pwd=plain_password,                      # ✅ raw password stored
        hashed_password=hash_password(plain_password),# ✅ hashed value
        is_active=True,
        active=True,                                  # if you want both
        is_hadmin=True,
        is_sadmin=False,
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
        "login_name": current_user.login_name,
    }
