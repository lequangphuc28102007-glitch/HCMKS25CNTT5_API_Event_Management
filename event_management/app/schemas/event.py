from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List

from app.schemas.event_staff import EventStaffResponse
from app.schemas.event_task import EventTaskResponse    

class EventBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    location: Optional[str] = None
    starts_at: datetime
    end_at: datetime


class EventCreate(EventBase):
    pass

class EventUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    location: Optional[str] = None
    starts_at: Optional[datetime] = None

class EventResponse(EventBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int

class EventDetail(EventResponse):
    staff: List[EventStaffResponse] = []
    tasks: List[EventTaskResponse] = []


class AddMemberRequest(BaseModel):
    user_id: int