from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.core.security import create_access_token, verify_password, create_refresh_token
from app.dependencies.auth import DbSession
from app.schemas.auth import Token
from app.schemas.user import UserCreate, UserResponse
from app.services.users import create_user, get_user_by_email
from app.db.database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])

login_attempts = {}  
MAX_ATTEMPTS = 5
WINDOW = timedelta(minutes=1)

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(data: UserCreate, db: DbSession):

    if get_user_by_email(db, data.email):
        raise HTTPException(status_code=409, detail="Email is already registered")
    return create_user(db, data)


@router.post("/login", response_model=Token)
def login(request: Request, db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    ip = request.client.host
    now = datetime.now()

    attempts = login_attempts.get(ip, [])
    attempts = [t for t in attempts if now - t < WINDOW]

    if len(attempts) >= MAX_ATTEMPTS:
        raise HTTPException(status_code=429, detail="Too many login attempts, please try later")

    attempts.append(now)
    login_attempts[ip] = attempts

    user = get_user_by_email(db, form_data.username)
    if (
        user is None
        or user.is_active != "active"
        or not verify_password(form_data.password, user.password_hash)
    ):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    user.refresh_token = refresh_token
    db.commit()

    return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")

