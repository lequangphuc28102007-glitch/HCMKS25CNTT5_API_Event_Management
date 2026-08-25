from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserCreate, UserResponse
from app.services.auth_service import login_user, register_user

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Đăng ký tài khoản",
    description="Tạo tài khoản mới. Email phải là duy nhất trong hệ thống.",
)
def register(data: UserCreate, db: Session = Depends(get_db)):
    return register_user(db, data)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Đăng nhập",
    description="Xác thực bằng email/password, trả về access token JWT.",
)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    token = login_user(db, data)
    return TokenResponse(access_token=token)
