from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.event_task import TaskPriority, TaskStatus


class EventTaskBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    due_date: datetime | None = None
    priority: TaskPriority = TaskPriority.MEDIUM


class EventTaskCreate(EventTaskBase):
    assignee_id: int | None = None


class EventTaskUpdate(BaseModel):
    """Tất cả field optional để hỗ trợ PATCH - chỉ ghi đè field được gửi lên."""

    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    due_date: datetime | None = None
    priority: TaskPriority | None = None
    status: TaskStatus | None = None
    assignee_id: int | None = None


class EventTaskResponse(EventTaskBase):
    id: int
    event_id: int
    assignee_id: int | None
    status: TaskStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
