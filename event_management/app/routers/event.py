from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.dependencies.auth import CurrentUser, DbSession
from app.models.event import Event
from app.schemas.event import EventCreate, EventResponse

router = APIRouter(prefix="/events", tags=["events"])


@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
def create_event(data: EventCreate, db: DbSession, current_user: CurrentUser):
    event = Event(**data.model_dump(), owner_id=current_user.id)
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


@router.get("", response_model=list[EventResponse])
def list_events(db: DbSession, current_user: CurrentUser):
    return list(db.scalars(select(Event).where(Event.owner_id == current_user.id)))


@router.get("/{event_id}", response_model=EventResponse)
def get_event(event_id: int, db: DbSession, current_user: CurrentUser):
    event = db.scalar(select(Event).where(Event.id == event_id, Event.owner_id == current_user.id))
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return event
