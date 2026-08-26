from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.permissions import require_admin
from app.models.user import User
from app.schemas.common import ErrorResponse, ValidationErrorResponse
from app.schemas.user import UserResponse
from app.services.user_service import search_users

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Xem hồ sơ cá nhân",
    description=(
        "Lấy thông tin tài khoản của người dùng đang đăng nhập dựa trên JWT Access Token.\n\n"
        "**Yêu cầu xác thực:**\n"
        "- Header: `Authorization: Bearer <access_token>`.\n"
        "- Không để lộ `password_hash` trong phản hồi."
    ),
    responses={
        status.HTTP_200_OK: {
            "model": UserResponse,
            "description": "Lấy thông tin cá nhân thành công.",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "model": ErrorResponse,
            "description": "Chưa đăng nhập, thiếu token hoặc token không hợp lệ / hết hạn.",
        },
    },
)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get(
    "",
    response_model=list[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="Tìm kiếm & Xem danh sách người dùng (Dành cho Admin)",
    description=(
        "Lấy danh sách người dùng trong hệ thống với các tiêu chí tìm kiếm và lọc.\n\n"
        "**Phân quyền:**\n"
        "- Chỉ người dùng có vai trò `ADMIN` mới được phép gọi API này (User thường sẽ nhận mã lỗi 403 Forbidden).\n\n"
        "**Bộ lọc hỗ trợ:**\n"
        "- `keyword`: Tìm kiếm không phân biệt hoa thường theo họ tên (`full_name`) hoặc `email`.\n"
        "- `is_active`: Lọc theo trạng thái tài khoản (`true`: đang hoạt động, `false`: đã bị khóa)."
    ),
    responses={
        status.HTTP_200_OK: {
            "model": list[UserResponse],
            "description": "Danh sách người dùng thỏa mãn điều kiện lọc.",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "model": ErrorResponse,
            "description": "Chưa xác thực hoặc token không hợp lệ.",
        },
        status.HTTP_403_FORBIDDEN: {
            "model": ErrorResponse,
            "description": "Chỉ quản trị viên (Admin) mới có quyền truy cập API này.",
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "model": ValidationErrorResponse,
            "description": "Tham số truy vấn (Query parameter) không đúng kiểu dữ liệu.",
        },
    },
)
def list_users(
    keyword: str | None = Query(default=None, description="Từ khóa tìm kiếm theo họ tên hoặc email"),
    is_active: bool | None = Query(default=None, description="Lọc theo trạng thái tài khoản (true/false)"),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    return search_users(db, keyword, is_active)
