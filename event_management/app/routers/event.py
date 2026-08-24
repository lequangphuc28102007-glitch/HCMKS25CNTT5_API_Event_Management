from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy import select, or_
from sqlalchemy.orm import Session, Query
from typing import List
from datetime import datetime

from app.db.database import get_db
from app.dependencies.auth import CurrentUser, DbSession, get_current_user
from app.models.event import Event
from app.models.event_staff import EventStaff
from app.models.event_history import EventHistory
from app.models.user import User
from app.schemas.event import EventCreate, EventResponse, AddMemberRequest


router = APIRouter(prefix="/events", tags=["events"])


@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
def create_event(data: EventCreate, db: DbSession, current_user: CurrentUser):
    if Event.end_time <= Event.start_time:
        raise HTTPException(status_code=400, detail="End time must be after start time")
    event = Event(**data.model_dump(), owner_id=current_user.id)
    db.add(event)
    db.commit()
    db.refresh(event)
    log_event_action(db, event.id, current_user.id, "CREATE_EVENT", f"Created event {event.title}")
    return event


@router.get("", response_model=list[EventResponse])
def list_events(db: DbSession, current_user: CurrentUser):
    return list(db.scalars(select(Event).where(Event.owner_id == current_user.id)))


@router.get("/events", response_model=List[EventResponse])
def get_events_by_search(
    search: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Event).where(
        or_(
            Event.owner_id == current_user.id,
            Event.id.in_(
                select(EventStaff.event_id).where(EventStaff.user_id == current_user.id)
            )
        )
    )

    if search:
        stmt = stmt.where(Event.title.ilike(f"%{search}%"))

    events = db.scalars(stmt).all()

    if not events:
        raise HTTPException(status_code=404, detail="No events found")

    return events

@router.get("/events/{event_id}", response_model=EventResponse)
def get_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Event).where(
        Event.is_deleted == False,
        or_(
            Event.owner_id == current_user.id,
            Event.id.in_(
                select(EventStaff.event_id).where(EventStaff.user_id == current_user.id)
            )
        )
    )

    event = db.scalar(stmt)

    if event is None:
        raise HTTPException(
            status_code=403,  
            detail="You are not allowed to view this event"
        )

    return event


@router.delete("/events/{event_id}")
def delete_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    if event.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only owner can delete event")

    event.is_deleted = True
    event.deleted_at = datetime.utcnow()
    db.commit()

    return {"message": "Event deleted (soft delete)", "event_id": event_id}



@router.post("/events/{event_id}/members")
def add_member(
    event_id: int,
    request: AddMemberRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if event.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only owner can add members")

    user_to_add = db.query(User).filter(User.id == request.user_id).first()
    if not user_to_add:
        raise HTTPException(status_code=404, detail="User not found")

    existing = db.query(EventStaff).filter(
        EventStaff.event_id == event_id,
        EventStaff.user_id == request.user_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already a member")

    new_member = EventStaff(event_id=event_id, user_id=request.user_id)
    db.add(new_member)
    db.commit()
    db.refresh(new_member)
    log_event_action(db, event_id, current_user.id, "ADD_MEMBER", f"Added user {request.user_id}")
    return {"message": "User added as member", "event_id": event_id, "user_id": request.user_id}

def log_event_action(db: Session, event_id: int, user_id: int, action: str, detail: str = None):
    history = EventHistory(
        event_id=event_id,
        user_id=user_id,
        action=action,
        detail=detail
    )
    db.add(history)
    db.commit()
