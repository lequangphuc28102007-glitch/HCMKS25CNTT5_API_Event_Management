from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.models import EventStaff, Event, User
from app.schemas.event_staff import EventStaffResponse
from app.dependencies.auth import get_current_user
from app.schemas.event_staff import AddMemberRequest

router = APIRouter(prefix="/event-staff", tags=["event_staff"])

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
    return {"message": "User added as member", "event_id": event_id, "user_id": request.user_id}

@router.delete("/events/{event_id}/members/{user_id}", status_code=204)
def remove_member(event_id: int, user_id: int, current_user: int = Depends(get_current_user), db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    owner = db.query(EventStaff).filter_by(event_id=event_id, user_id=current_user, role="owner").first()
    if not owner:
        raise HTTPException(status_code=403, detail="Only owner can remove members")

    member = db.query(EventStaff).filter_by(event_id=event_id, user_id=user_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    if member.role == "owner":
        owners_count = db.query(EventStaff).filter_by(event_id=event_id, role="owner").count()
        if owners_count <= 1:
            raise HTTPException(status_code=409, detail="Cannot remove the last owner")

    db.delete(member)
    db.commit()
    return {"detail": "Member removed successfully"}

@router.get("/events/{event_id}/members")
def get_event_members(event_id: int, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    members = db.query(EventStaff).filter(EventStaff.event_id == event_id).all()

    return [
        {
            "user_id": member.user_id,
            "role": member.role
        }
        for member in members
    ]
