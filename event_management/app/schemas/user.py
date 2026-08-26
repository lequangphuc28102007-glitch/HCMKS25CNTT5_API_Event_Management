from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.user import UserRole


class UserBase(BaseModel):
    email: EmailStr = Field(..., description="Địa chỉ email duy nhất của người dùng", example="user@example.com")
    full_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Họ và tên đầy đủ của người dùng",
        example="Nguyễn Văn A",
    )

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Họ và tên không được để trống hoặc chỉ chứa khoảng trắng")
        return stripped


class UserCreate(UserBase):
    password: str = Field(
        ...,
        min_length=6,
        max_length=128,
        description="Mật khẩu tài khoản (tối thiểu 6 ký tự)",
        example="password123",
    )


class UserResponse(UserBase):
    id: int = Field(..., description="Mã định danh duy nhất của người dùng", example=1)
    role: UserRole = Field(..., description="Vai trò hệ thống (USER hoặc ADMIN)", example=UserRole.USER)
    is_active: bool = Field(..., description="Trạng thái tài khoản (True: hoạt động, False: bị khóa)", example=True)
    created_at: datetime = Field(..., description="Thời gian tạo tài khoản")

    model_config = ConfigDict(from_attributes=True)
