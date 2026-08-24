from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.models import EventStaff, Event, User
from app.schemas.event_staff import EventStaffResponse
from app.dependencies.auth import get_current_user

router = APIRouter(prefix="/events/{event_id}/staff", tags=["event_staff"])

@router.post("/", response_model=EventStaffResponse)
def add_staff(event_id: int, user_id: int, role: str = "MEMBER", db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Sự kiện không tồn tại")
    exists = db.query(EventStaff).filter(EventStaff.event_id == event_id, EventStaff.user_id == user_id).first()
    if exists:
        raise HTTPException(status_code=400, detail="User đã là staff")
    staff = EventStaff(event_id=event_id, user_id=user_id, role=role)
    db.add(staff)
    db.commit()
    db.refresh(staff)
    return staff

@router.get("/", response_model=List[EventStaffResponse])
def list_staff(event_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(EventStaff).filter(EventStaff.event_id == event_id).all()

@router.delete("/{user_id}")
def remove_staff(event_id: int, user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    staff = db.query(EventStaff).filter(EventStaff.event_id == event_id, EventStaff.user_id == user_id).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff không tồn tại")
    if staff.role == "OWNER":
        raise HTTPException(status_code=400, detail="Không được xóa OWNER cuối cùng")
    db.delete(staff)
    db.commit()
    return {"detail": "Đã xóa staff"}
