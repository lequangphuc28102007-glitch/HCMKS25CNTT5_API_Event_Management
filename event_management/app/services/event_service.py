from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestException, NotFoundException
from app.models.event import Event, EventStaff, EventStaffRole
from app.models.event_task import EventTask
from app.models.user import User
from app.schemas.event import EventCreate, EventUpdate


def create_event(db: Session, data: EventCreate, current_user: User) -> Event:
    event = Event(name=data.name, description=data.description, owner_id=current_user.id)
    db.add(event)
    db.flush()

    owner_staff = EventStaff(event_id=event.id, user_id=current_user.id, role=EventStaffRole.OWNER)
    db.add(owner_staff)

    db.commit()
    db.refresh(event)
    return event


def list_my_events(db: Session, current_user: User, search: str | None) -> list[Event]:
    query = (
        db.query(Event)
        .join(EventStaff, EventStaff.event_id == Event.id)
        .filter(EventStaff.user_id == current_user.id)
    )

    if search:
        search_term = search.strip()
        if search_term:
            query = query.filter(Event.name.ilike(f"%{search_term}%"))

    return query.order_by(Event.created_at.desc()).all()


def update_event(db: Session, event: Event, data: EventUpdate) -> Event:
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(event, field, value)

    db.commit()
    db.refresh(event)
    return event


def delete_event(db: Session, event: Event) -> None:
    db.delete(event)
    db.commit()


def add_member(db: Session, event: Event, user_id: int) -> EventStaff:
    user = db.get(User, user_id)
    if user is None:
        raise NotFoundException("Người dùng cần thêm không tồn tại")
    if not user.is_active:
        raise BadRequestException("Tài khoản người dùng đã bị vô hiệu hóa")

    existing = (
        db.query(EventStaff)
        .filter(EventStaff.event_id == event.id, EventStaff.user_id == user_id)
        .first()
    )
    if existing:
        raise BadRequestException("Người dùng này đã là thành viên của sự kiện")

    staff = EventStaff(event_id=event.id, user_id=user_id, role=EventStaffRole.MEMBER)
    db.add(staff)
    db.commit()
    db.refresh(staff)
    return staff


def list_members(db: Session, event_id: int) -> list[EventStaff]:
    return db.query(EventStaff).filter(EventStaff.event_id == event_id).all()


def remove_member(db: Session, event: Event, user_id: int) -> None:
    staff = (
        db.query(EventStaff)
        .filter(EventStaff.event_id == event.id, EventStaff.user_id == user_id)
        .first()
    )
    if staff is None:
        raise NotFoundException("Thành viên không tồn tại trong sự kiện")

    if staff.role == EventStaffRole.OWNER:
        raise BadRequestException("Không thể xóa owner của sự kiện")

    # Unassign tasks in this event assigned to the removed member
    db.query(EventTask).filter(
        EventTask.event_id == event.id, EventTask.assignee_id == user_id
    ).update({EventTask.assignee_id: None})

    db.delete(staff)
    db.commit()
