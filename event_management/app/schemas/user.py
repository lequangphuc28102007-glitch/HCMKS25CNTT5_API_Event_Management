from pydantic import BaseModel
from enum import Enum

class UserRole(str, Enum):
    USER = "USER"
    ADMIN = "ADMIN"

class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"

class UserBase(BaseModel):
    email: str
    full_name: str

class UserCreate(UserBase):
    password: str

class UserUpdate(UserBase):
    pass

class UserResponse(UserBase):
    id: int
    role: UserRole
    is_active: UserStatus

    model_config = {"from_attributes": True}
