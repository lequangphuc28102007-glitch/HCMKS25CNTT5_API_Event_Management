from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenException, NotFoundException
from app.db.database import get_db
from app.dependencies.auth import get_current_user
from app.models.event import Event, EventStaff, EventStaffRole
from app.models.user import User, UserRole


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.ADMIN:
        raise ForbiddenException("Chỉ Admin mới có quyền thực hiện thao tác này")
    return current_user


def get_event_or_404(event_id: int, db: Session) -> Event:
    event = db.get(Event, event_id)
    if event is None:
        raise NotFoundException("Sự kiện không tồn tại")
    return event


def get_membership(db: Session, event_id: int, user_id: int) -> EventStaff | None:
    return (
        db.query(EventStaff)
        .filter(EventStaff.event_id == event_id, EventStaff.user_id == user_id)
        .first()
    )


def require_event_member(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Event:
    event = get_event_or_404(event_id, db)
    membership = get_membership(db, event_id, current_user.id)
    if membership is None:
        raise ForbiddenException("Bạn không phải thành viên của sự kiện này")
    return event


def require_event_owner(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Event:
    event = get_event_or_404(event_id, db)
    if event.owner_id != current_user.id:
        raise ForbiddenException("Chỉ chủ sự kiện (owner) mới có quyền thực hiện thao tác này")
    return event
