from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole


class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=255)


class UserCreate(UserBase):
    """Dùng cho POST /auth/register"""

    password: str = Field(min_length=6, max_length=128)


class UserResponse(UserBase):
    """Trả về cho client - KHÔNG bao giờ chứa password_hash"""

    id: int
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
