# app/routers/users.py

import os
from fastapi import APIRouter, Depends, HTTPException
import jwt
from sqlalchemy.orm import Session
from app.models.database import SessionLocal
from app.models.all_models import User
from app.schemas.all import UserLogin, UserRegister
from app.utils.security import hash_password, verify_password, create_access_token
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError


router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/login")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


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


def get_current_user(token: str = Depends(oauth2_scheme)):
    print(f"📦 Raw token string: {token}")

    credentials_exception = HTTPException(status_code=401, detail="Invalid token")

    try:
        # ✅ Remove "Bearer " prefix if present
        if token.startswith("Bearer "):
            token = token.split(" ")[1]

        payload = jwt.decode(token, os.getenv('SECRET_TOKEN'), algorithms=[os.getenv('ALGORITHM')])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError as e:
        print(f"❌ Token decode error: {e}")
        raise credentials_exception

    db = SessionLocal()
    user = db.query(User).filter(User.id == int(user_id)).first()
    db.close()

    if user is None:
        raise credentials_exception

    print(f"✅ Authenticated user: {user.fullname} (ID: {user.id})")
    return user

# to get the current admin user
def get_current_admin_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, os.getenv("SECRET_TOKEN"), algorithms=[os.getenv("ALGORITHM")])
        user_role = payload.get("role")  # assumes token includes a 'role' claim
        if user_role != "admin":
            raise HTTPException(status_code=403, detail="Not authorized")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    

def login_required(user: User = Depends(get_current_user)) -> User:
    return user

@router.get("/user_profile")
def read_users_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "fullname": current_user.fullname,
        "mobile": current_user.mobile,
    }

def admin_required(user: User = Depends(get_current_user)) -> User:
    if not user.admin:
        raise HTTPException(status_code=403, detail="Admin access only")
    return user
