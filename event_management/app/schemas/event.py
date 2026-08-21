from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EventCreate(BaseModel):
    title: str
    description: str | None = None
    location: str | None = None
    starts_at: datetime


class EventResponse(EventCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
