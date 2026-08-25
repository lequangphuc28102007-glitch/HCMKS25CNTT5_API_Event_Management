from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.permissions import require_event_member, require_event_owner
from app.models.event import Event
from app.models.user import User
from app.schemas.event import (
    EventCreate,
    EventMemberAdd,
    EventMemberResponse,
    EventResponse,
    EventUpdate,
)
from app.services import event_service

router = APIRouter(prefix="/events", tags=["Events"])


@router.post(
    "",
    response_model=EventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo sự kiện",
    description="User đăng nhập tạo sự kiện mới và tự động trở thành OWNER.",
)
def create_event(
    data: EventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return event_service.create_event(db, data, current_user)


@router.get(
    "",
    response_model=list[EventResponse],
    summary="Danh sách sự kiện của tôi",
    description="Chỉ trả về sự kiện mà user hiện tại là owner hoặc member. Hỗ trợ search theo tên.",
)
def list_events(
    search: str | None = Query(default=None, description="Tìm theo tên sự kiện"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return event_service.list_my_events(db, current_user, search)


@router.get(
    "/{event_id}",
    response_model=EventResponse,
    summary="Chi tiết sự kiện",
    description="Chỉ thành viên (owner/member) của sự kiện mới được xem.",
)
def get_event(event: Event = Depends(require_event_member)):
    return event


@router.patch(
    "/{event_id}",
    response_model=EventResponse,
    summary="Cập nhật sự kiện (PATCH)",
    description="Chỉ OWNER được sửa. Chỉ cập nhật field được gửi lên.",
)
@router.put(
    "/{event_id}",
    response_model=EventResponse,
    summary="Cập nhật sự kiện (PUT)",
    description="Chỉ OWNER được sửa. Chỉ cập nhật field được gửi lên.",
)
def update_event(
    data: EventUpdate,
    event: Event = Depends(require_event_owner),
    db: Session = Depends(get_db),
):
    return event_service.update_event(db, event, data)


@router.delete(
    "/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Xóa sự kiện",
    description="Chỉ OWNER được xóa.",
)
def delete_event(
    event: Event = Depends(require_event_owner),
    db: Session = Depends(get_db),
):
    event_service.delete_event(db, event)


@router.post(
    "/{event_id}/members",
    response_model=EventMemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Thêm thành viên",
    description="Chỉ OWNER được thêm. Không cho thêm thành viên trùng.",
)
def add_member(
    data: EventMemberAdd,
    event: Event = Depends(require_event_owner),
    db: Session = Depends(get_db),
):
    return event_service.add_member(db, event, data.user_id)


@router.get(
    "/{event_id}/members",
    response_model=list[EventMemberResponse],
    summary="Danh sách thành viên",
    description="Chỉ thành viên sự kiện mới được xem, trả role của từng người trong sự kiện.",
)
def list_members(
    event: Event = Depends(require_event_member),
    db: Session = Depends(get_db),
):
    return event_service.list_members(db, event.id)


@router.delete(
    "/{event_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Xóa thành viên",
    description="Chỉ OWNER được xóa. Không được xóa owner cuối cùng của sự kiện.",
)
def remove_member(
    user_id: int,
    event: Event = Depends(require_event_owner),
    db: Session = Depends(get_db),
):
    event_service.remove_member(db, event, user_id)
