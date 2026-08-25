from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.permissions import require_event_member
from app.models.event import Event
from app.models.event_task import TaskPriority, TaskStatus
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.event_task import EventTaskCreate, EventTaskResponse, EventTaskUpdate
from app.services import event_task_service

router = APIRouter(tags=["Event Tasks"])


@router.post(
    "/events/{event_id}/event-tasks",
    response_model=EventTaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo công việc sự kiện",
    description="Thành viên sự kiện tạo công việc với title, description, due_date, priority.",
)
def create_task(
    data: EventTaskCreate,
    event: Event = Depends(require_event_member),
    db: Session = Depends(get_db),
):
    return event_task_service.create_task(db, event, data)


@router.get(
    "/events/{event_id}/event-tasks",
    response_model=PaginatedResponse[EventTaskResponse],
    summary="Danh sách công việc sự kiện",
    description=(
        "Trả công việc thuộc sự kiện, hỗ trợ filter theo status/priority/assignee, "
        "search theo title, phân trang page/size, sort theo created_at hoặc due_date."
    ),
)
def list_tasks(
    event: Event = Depends(require_event_member),
    status_filter: TaskStatus | None = Query(default=None, alias="status"),
    priority: TaskPriority | None = Query(default=None),
    assignee_id: int | None = Query(default=None),
    search: str | None = Query(default=None, description="Tìm theo title"),
    sort_by: str = Query(default="created_at", pattern="^(created_at|due_date)$"),
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    items, total = event_task_service.list_tasks(
        db, event.id, status_filter, priority, assignee_id, search, sort_by, sort_order, page, size
    )
    return PaginatedResponse(total=total, page=page, size=size, items=items)


@router.get(
    "/event-tasks/{task_id}",
    response_model=EventTaskResponse,
    summary="Chi tiết công việc sự kiện",
    description="Kiểm tra user thuộc sự kiện chứa công việc trước khi trả dữ liệu.",
)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = event_task_service.get_task_in_event_or_404(db, task_id)
    event_task_service.check_member_of_task_event(db, task, current_user)
    return task


@router.patch(
    "/event-tasks/{task_id}",
    response_model=EventTaskResponse,
    summary="Cập nhật công việc sự kiện",
    description="Chỉ owner của sự kiện hoặc assignee của công việc được cập nhật. Chỉ ghi đè field được gửi lên.",
)
def update_task(
    task_id: int,
    data: EventTaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = event_task_service.get_task_in_event_or_404(db, task_id)
    event_task_service.check_member_of_task_event(db, task, current_user)
    event_task_service.check_can_modify_task(db, task, current_user)
    event = db.get(Event, task.event_id)
    return event_task_service.update_task(db, event, task, data)


@router.delete(
    "/event-tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Xóa công việc sự kiện",
    description="Chỉ owner của sự kiện hoặc assignee của công việc được xóa.",
)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = event_task_service.get_task_in_event_or_404(db, task_id)
    event_task_service.check_member_of_task_event(db, task, current_user)
    event_task_service.check_can_modify_task(db, task, current_user)
    event_task_service.delete_task(db, task)
