from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestException, ForbiddenException, NotFoundException
from app.dependencies.permissions import get_membership
from app.models.event import Event
from app.models.event_task import EventTask, TaskPriority, TaskStatus
from app.models.user import User
from app.schemas.event_task import EventTaskCreate, EventTaskUpdate

ALLOWED_SORT_FIELDS = {"created_at": EventTask.created_at, "due_date": EventTask.due_date}


def create_task(db: Session, event: Event, data: EventTaskCreate) -> EventTask:
    if data.assignee_id is not None:
        user = db.get(User, data.assignee_id)
        if user is None or not user.is_active:
            raise BadRequestException("Người được giao việc không tồn tại hoặc đã bị vô hiệu hóa")
        membership = get_membership(db, event.id, data.assignee_id)
        if membership is None:
            raise BadRequestException("Người được giao việc phải là thành viên của sự kiện")

    task = EventTask(
        event_id=event.id,
        title=data.title,
        description=data.description,
        due_date=data.due_date,
        priority=data.priority,
        assignee_id=data.assignee_id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def list_tasks(
    db: Session,
    event_id: int,
    status_filter: TaskStatus | None,
    priority_filter: TaskPriority | None,
    assignee_id: int | None,
    search: str | None,
    sort_by: str,
    sort_order: str,
    page: int,
    size: int,
) -> tuple[list[EventTask], int]:
    query = db.query(EventTask).filter(EventTask.event_id == event_id)

    if status_filter is not None:
        query = query.filter(EventTask.status == status_filter)
    if priority_filter is not None:
        query = query.filter(EventTask.priority == priority_filter)
    if assignee_id is not None:
        query = query.filter(EventTask.assignee_id == assignee_id)
    if search:
        search_term = search.strip()
        if search_term:
            query = query.filter(EventTask.title.ilike(f"%{search_term}%"))

    total = query.count()

    sort_key = sort_by.strip().lower() if sort_by else "created_at"
    sort_column = ALLOWED_SORT_FIELDS.get(sort_key, EventTask.created_at)
    order_func = desc if (sort_order and sort_order.strip().lower() == "desc") else asc
    query = query.order_by(order_func(sort_column))

    items = query.offset((page - 1) * size).limit(size).all()
    return items, total


def get_task_in_event_or_404(db: Session, task_id: int) -> EventTask:
    task = db.get(EventTask, task_id)
    if task is None:
        raise NotFoundException("Công việc sự kiện không tồn tại")
    return task


def check_member_of_task_event(db: Session, task: EventTask, current_user: User) -> None:
    membership = get_membership(db, task.event_id, current_user.id)
    if membership is None:
        raise ForbiddenException("Bạn không phải thành viên của sự kiện chứa công việc này")


def check_can_modify_task(db: Session, task: EventTask, current_user: User) -> None:
    event = db.get(Event, task.event_id)
    if event is None:
        raise NotFoundException("Sự kiện chứa công việc này không tồn tại")

    is_owner = event.owner_id == current_user.id
    is_assignee = task.assignee_id is not None and task.assignee_id == current_user.id

    if not (is_owner or is_assignee):
        raise ForbiddenException("Bạn không có quyền sửa/xóa công việc này")


def update_task(db: Session, event: Event, task: EventTask, data: EventTaskUpdate) -> EventTask:
    update_data = data.model_dump(exclude_unset=True)

    if "assignee_id" in update_data and update_data["assignee_id"] is not None:
        user = db.get(User, update_data["assignee_id"])
        if user is None or not user.is_active:
            raise BadRequestException("Người được giao việc không tồn tại hoặc đã bị vô hiệu hóa")
        membership = get_membership(db, event.id, update_data["assignee_id"])
        if membership is None:
            raise BadRequestException("Người được giao việc phải là thành viên của sự kiện")

    for field, value in update_data.items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)
    return task


def delete_task(db: Session, task: EventTask) -> None:
    db.delete(task)
    db.commit()
