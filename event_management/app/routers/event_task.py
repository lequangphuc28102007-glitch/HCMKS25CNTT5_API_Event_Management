from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.dependencies.auth import CurrentUser, DbSession
from app.models.event import Event
from app.models.event_task import EventTask
from app.schemas.event_task import EventTaskCreate, EventTaskResponse

router = APIRouter(prefix="/events/{event_id}/tasks", tags=["event-tasks"])


def owned_event(db: DbSession, event_id: int, user_id: int) -> Event:
    event = db.scalar(select(Event).where(Event.id == event_id, Event.owner_id == user_id))
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.post("", response_model=EventTaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(event_id: int, data: EventTaskCreate, db: DbSession, current_user: CurrentUser):
    owned_event(db, event_id, current_user.id)
    task = EventTask(event_id=event_id, title=data.title)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("", response_model=list[EventTaskResponse])
def list_tasks(event_id: int, db: DbSession, current_user: CurrentUser):
    owned_event(db, event_id, current_user.id)
    return list(db.scalars(select(EventTask).where(EventTask.event_id == event_id)))
