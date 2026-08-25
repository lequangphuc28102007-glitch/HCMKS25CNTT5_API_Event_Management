from pydantic import BaseModel
from typing import Literal

class EventStaffBase(BaseModel):
    role: Literal["OWNER", "MEMBER"] = "MEMBER"

class EventStaffResponse(EventStaffBase):
    id: int
    event_id: int
    user_id: int

    class Config:
        from_attributes = True


class AddMemberRequest(BaseModel):
    user_id: int