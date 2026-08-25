from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.permissions import require_admin
from app.models.user import User
from app.schemas.user import UserResponse
from app.services.user_service import search_users

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Xem hồ sơ cá nhân",
    description="Trả về thông tin của user đang đăng nhập (không lộ password_hash).",
)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get(
    "",
    response_model=list[UserResponse],
    summary="Danh sách người dùng (Admin)",
    description="Chỉ Admin được xem. Hỗ trợ search theo tên/email và lọc theo trạng thái is_active.",
)
def list_users(
    keyword: str | None = Query(default=None, description="Từ khóa tìm theo tên hoặc email"),
    is_active: bool | None = Query(default=None, description="Lọc theo trạng thái tài khoản"),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    return search_users(db, keyword, is_active)
