from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.models import EventTask, Event
from app.schemas.event_task import EventTaskCreate, EventTaskUpdate, EventTaskResponse
from app.dependencies.auth import get_current_user
from app.models import User
from app.routers.event import log_event_action

router = APIRouter(prefix="/events/{event_id}/tasks", tags=["event_tasks"])

@router.post("/", response_model=EventTaskResponse)
def create_task(event_id: int, task_in: EventTaskCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Sự kiện không tồn tại")
    task = EventTask(event_id=event_id, **task_in.dict())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

@router.get("/", response_model=List[EventTaskResponse])
def list_tasks(event_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(EventTask).filter(EventTask.event_id == event_id).all()

@router.patch("/{task_id}", response_model=EventTaskResponse)
def update_task(event_id: int, task_id: int, task_in: EventTaskUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    task = db.query(EventTask).filter(EventTask.id == task_id, EventTask.event_id == event_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task không tồn tại")
    for field, value in task_in.dict(exclude_unset=True).items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    log_event_action(db, task.id, current_user.id, "UPDATE_EVENT", "Updated event title")

    return task

@router.delete("/{task_id}")
def delete_task(event_id: int, task_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    task = db.query(EventTask).filter(EventTask.id == task_id, EventTask.event_id == event_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task không tồn tại")
    db.delete(task)
    db.commit()
    log_event_action(db, event_id, current_user.id, "REMOVE_MEMBER", f"Removed user {task.user_id}")

    return {"detail": "Đã xóa task"}
