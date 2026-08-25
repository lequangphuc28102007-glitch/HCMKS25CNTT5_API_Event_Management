from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.event import EventStaffRole
from app.schemas.user import UserResponse


class EventBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None


class EventCreate(EventBase):
    pass


class EventUpdate(BaseModel):
    """Tất cả field optional để hỗ trợ PATCH - chỉ cập nhật field được gửi lên."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None


class EventResponse(EventBase):
    id: int
    owner_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EventMemberAdd(BaseModel):
    user_id: int


class EventMemberResponse(BaseModel):
    user_id: int
    role: EventStaffRole
    joined_at: datetime
    user: UserResponse

    model_config = ConfigDict(from_attributes=True)
