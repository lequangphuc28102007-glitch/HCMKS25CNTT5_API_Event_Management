from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.event import EventStaffRole
from app.schemas.user import UserResponse


class EventBase(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Tên sự kiện",
        example="Hội thảo Công nghệ 2026",
    )
    description: str | None = Field(
        default=None,
        description="Mô tả chi tiết nội dung sự kiện",
        example="Hội thảo chuyên sâu về Trí tuệ nhân tạo và Điện toán đám mây.",
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Tên sự kiện không được để trống hoặc chỉ chứa khoảng trắng")
        return stripped


class EventCreate(EventBase):
    pass


class EventUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Tên mới của sự kiện",
        example="Hội thảo Công nghệ Đổi mới 2026",
    )
    description: str | None = Field(
        default=None,
        description="Mô tả mới của sự kiện",
        example="Cập nhật chương trình hội thảo với sự tham gia của các chuyên gia quốc tế.",
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str | None) -> str | None:
        if v is not None:
            stripped = v.strip()
            if not stripped:
                raise ValueError("Tên sự kiện không được để trống hoặc chỉ chứa khoảng trắng")
            return stripped
        return v


class EventResponse(EventBase):
    id: int = Field(..., description="Mã định danh duy nhất của sự kiện", example=1)
    owner_id: int = Field(..., description="ID của người tạo (OWNER) sự kiện", example=1)
    created_at: datetime = Field(..., description="Thời gian tạo sự kiện")

    model_config = ConfigDict(from_attributes=True)


class EventMemberAdd(BaseModel):
    user_id: int = Field(..., description="ID của người dùng cần thêm vào sự kiện", example=2)


class EventMemberResponse(BaseModel):
    user_id: int = Field(..., description="ID của thành viên", example=2)
    role: EventStaffRole = Field(..., description="Vai trò trong sự kiện (OWNER hoặc MEMBER)", example=EventStaffRole.MEMBER)
    joined_at: datetime = Field(..., description="Thời gian tham gia sự kiện")
    user: UserResponse = Field(..., description="Thông tin chi tiết của người dùng")

    model_config = ConfigDict(from_attributes=True)
