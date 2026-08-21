from pydantic import BaseModel, ConfigDict


class EventTaskCreate(BaseModel):
    title: str


class EventTaskResponse(EventTaskCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: int
    is_completed: bool
