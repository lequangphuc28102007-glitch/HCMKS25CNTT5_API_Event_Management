from enum import Enum
from datetime import datetime

from pydantic import BaseModel, ConfigDict
from typing import Optional

class TaskStatus(str, Enum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"


class TaskPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class EventTaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    deadline: Optional[datetime] = None

class EventTaskCreate(EventTaskBase):
    pass

class EventTaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    deadline: Optional[datetime] = None


class EventTaskResponse(EventTaskCreate):

    id: int
    event_id: int

    model_config = ConfigDict(from_attributes=True)
