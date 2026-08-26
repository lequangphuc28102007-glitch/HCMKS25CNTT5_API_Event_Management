from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.permissions import require_event_member, require_event_owner
from app.models.event import Event
from app.models.user import User
from app.schemas.common import ErrorResponse, ValidationErrorResponse
from app.schemas.event import (
    EventCreate,
    EventMemberAdd,
    EventMemberResponse,
    EventResponse,
    EventUpdate,
)
from app.services import event_service

router = APIRouter(prefix="/events")


# ============================================================================
# EVENT CRUD ENDPOINTS (Tag: Events)
# ============================================================================


@router.post(
    "",
    response_model=EventResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Events"],
    summary="Tạo sự kiện mới",
    description=(
        "Người dùng đã đăng nhập tạo một sự kiện mới.\n\n"
        "**Quy tắc nghiệp vụ:**\n"
        "- Người tạo sẽ tự động được gán vai trò `OWNER` trong bảng thành viên sự kiện (`event_staff`).\n"
        "- `name` là bắt buộc, không được để trống hoặc chỉ chứa khoảng trắng.\n"
        "- `description` là trường tùy chọn."
    ),
    responses={
        status.HTTP_201_CREATED: {
            "model": EventResponse,
            "description": "Tạo sự kiện thành công, trả về thông tin sự kiện vừa tạo.",
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": "Dữ liệu không hợp lệ.",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "model": ErrorResponse,
            "description": "Chưa đăng nhập hoặc token không hợp lệ.",
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "model": ValidationErrorResponse,
            "description": "Dữ liệu gửi lên sai định dạng.",
        },
    },
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
    status_code=status.HTTP_200_OK,
    tags=["Events"],
    summary="Danh sách sự kiện của tôi",
    description=(
        "Lấy danh sách tất cả các sự kiện mà người dùng hiện tại đang tham gia (với vai trò `OWNER` hoặc `MEMBER`).\n\n"
        "**Tìm kiếm:**\n"
        "- Hỗ trợ tham số `search` để tìm kiếm không phân biệt hoa thường theo tên sự kiện."
    ),
    responses={
        status.HTTP_200_OK: {
            "model": list[EventResponse],
            "description": "Danh sách các sự kiện của người dùng.",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "model": ErrorResponse,
            "description": "Chưa đăng nhập hoặc token không hợp lệ.",
        },
    },
)
def list_events(
    search: str | None = Query(default=None, description="Từ khóa tìm kiếm theo tên sự kiện"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return event_service.list_my_events(db, current_user, search)


@router.get(
    "/{event_id}",
    response_model=EventResponse,
    status_code=status.HTTP_200_OK,
    tags=["Events"],
    summary="Xem chi tiết sự kiện",
    description=(
        "Lấy thông tin chi tiết của một sự kiện theo `event_id`.\n\n"
        "**Phân quyền:**\n"
        "- Chỉ người dùng là thành viên (`OWNER` hoặc `MEMBER`) của sự kiện mới được phép xem."
    ),
    responses={
        status.HTTP_200_OK: {
            "model": EventResponse,
            "description": "Thông tin chi tiết sự kiện.",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "model": ErrorResponse,
            "description": "Chưa đăng nhập hoặc token không hợp lệ.",
        },
        status.HTTP_403_FORBIDDEN: {
            "model": ErrorResponse,
            "description": "Bạn không phải thành viên của sự kiện này.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Sự kiện không tồn tại.",
        },
    },
)
def get_event(event: Event = Depends(require_event_member)):
    return event


@router.patch(
    "/{event_id}",
    response_model=EventResponse,
    status_code=status.HTTP_200_OK,
    tags=["Events"],
    summary="Cập nhật sự kiện (PATCH)",
    description=(
        "Cập nhật từng phần thông tin sự kiện (tên, mô tả).\n\n"
        "**Phân quyền:**\n"
        "- Chỉ `OWNER` của sự kiện mới có quyền chỉnh sửa."
    ),
    responses={
        status.HTTP_200_OK: {
            "model": EventResponse,
            "description": "Cập nhật sự kiện thành công.",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "model": ErrorResponse,
            "description": "Chưa đăng nhập hoặc token không hợp lệ.",
        },
        status.HTTP_403_FORBIDDEN: {
            "model": ErrorResponse,
            "description": "Chỉ chủ sự kiện (OWNER) mới có quyền chỉnh sửa.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Sự kiện không tồn tại.",
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "model": ValidationErrorResponse,
            "description": "Dữ liệu cập nhật không hợp lệ.",
        },
    },
)
@router.put(
    "/{event_id}",
    response_model=EventResponse,
    status_code=status.HTTP_200_OK,
    tags=["Events"],
    summary="Cập nhật sự kiện (PUT)",
    description=(
        "Cập nhật toàn bộ/từng phần thông tin sự kiện.\n\n"
        "**Phân quyền:**\n"
        "- Chỉ `OWNER` của sự kiện mới có quyền chỉnh sửa."
    ),
    responses={
        status.HTTP_200_OK: {
            "model": EventResponse,
            "description": "Cập nhật sự kiện thành công.",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "model": ErrorResponse,
            "description": "Chưa đăng nhập hoặc token không hợp lệ.",
        },
        status.HTTP_403_FORBIDDEN: {
            "model": ErrorResponse,
            "description": "Chỉ chủ sự kiện (OWNER) mới có quyền chỉnh sửa.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Sự kiện không tồn tại.",
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "model": ValidationErrorResponse,
            "description": "Dữ liệu cập nhật không hợp lệ.",
        },
    },
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
    tags=["Events"],
    summary="Xóa sự kiện",
    description=(
        "Xóa vĩnh viễn sự kiện và toàn bộ dữ liệu liên quan (thành viên, công việc con).\n\n"
        "**Phân quyền:**\n"
        "- Chỉ `OWNER` của sự kiện mới có quyền xóa."
    ),
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": "Xóa sự kiện thành công (không có nội dung trả về).",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "model": ErrorResponse,
            "description": "Chưa đăng nhập hoặc token không hợp lệ.",
        },
        status.HTTP_403_FORBIDDEN: {
            "model": ErrorResponse,
            "description": "Chỉ chủ sự kiện (OWNER) mới có quyền xóa.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Sự kiện không tồn tại.",
        },
    },
)
def delete_event(
    event: Event = Depends(require_event_owner),
    db: Session = Depends(get_db),
):
    event_service.delete_event(db, event)


# ============================================================================
# EVENT MEMBERS ENDPOINTS (Tag: Event Members)
# ============================================================================


@router.post(
    "/{event_id}/members",
    response_model=EventMemberResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Event Members"],
    summary="Thêm thành viên vào sự kiện",
    description=(
        "Thêm một người dùng hiện có vào sự kiện với vai trò `MEMBER`.\n\n"
        "**Quy tắc nghiệp vụ & Phân quyền:**\n"
        "- Chỉ `OWNER` của sự kiện mới có quyền thêm thành viên.\n"
        "- `user_id` phải tồn tại trong hệ thống và tài khoản đang hoạt động (`is_active=True`).\n"
        "- Không thể thêm người dùng đã là thành viên của sự kiện (báo lỗi 400)."
    ),
    responses={
        status.HTTP_201_CREATED: {
            "model": EventMemberResponse,
            "description": "Thêm thành viên vào sự kiện thành công.",
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": "Người dùng đã là thành viên hoặc tài khoản bị vô hiệu hóa.",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "model": ErrorResponse,
            "description": "Chưa đăng nhập hoặc token không hợp lệ.",
        },
        status.HTTP_403_FORBIDDEN: {
            "model": ErrorResponse,
            "description": "Chỉ chủ sự kiện (OWNER) mới có quyền thêm thành viên.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Sự kiện hoặc người dùng cần thêm không tồn tại.",
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "model": ValidationErrorResponse,
            "description": "Dữ liệu gửi lên sai định dạng.",
        },
    },
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
    status_code=status.HTTP_200_OK,
    tags=["Event Members"],
    summary="Danh sách thành viên sự kiện",
    description=(
        "Lấy danh sách tất cả thành viên tham gia sự kiện kèm vai trò (`OWNER` hoặc `MEMBER`) và thời gian tham gia.\n\n"
        "**Phân quyền:**\n"
        "- Chỉ thành viên (`OWNER` hoặc `MEMBER`) của sự kiện mới được xem danh sách này."
    ),
    responses={
        status.HTTP_200_OK: {
            "model": list[EventMemberResponse],
            "description": "Danh sách thành viên của sự kiện.",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "model": ErrorResponse,
            "description": "Chưa đăng nhập hoặc token không hợp lệ.",
        },
        status.HTTP_403_FORBIDDEN: {
            "model": ErrorResponse,
            "description": "Bạn không phải thành viên của sự kiện này.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Sự kiện không tồn tại.",
        },
    },
)
def list_members(
    event: Event = Depends(require_event_member),
    db: Session = Depends(get_db),
):
    return event_service.list_members(db, event.id)


@router.delete(
    "/{event_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Event Members"],
    summary="Xóa thành viên khỏi sự kiện",
    description=(
        "Xóa một thành viên ra khỏi sự kiện.\n\n"
        "**Quy tắc nghiệp vụ & Phân quyền:**\n"
        "- Chỉ `OWNER` của sự kiện mới có quyền xóa thành viên.\n"
        "- Không thể xóa `OWNER` của sự kiện (báo lỗi 400).\n"
        "- Khi thành viên bị xóa, các công việc đang gán cho người này trong sự kiện sẽ tự động chuyển về trạng thái chưa phân công (`assignee_id = null`)."
    ),
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": "Xóa thành viên khỏi sự kiện thành công.",
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": "Không thể xóa OWNER của sự kiện.",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "model": ErrorResponse,
            "description": "Chưa đăng nhập hoặc token không hợp lệ.",
        },
        status.HTTP_403_FORBIDDEN: {
            "model": ErrorResponse,
            "description": "Chỉ chủ sự kiện (OWNER) mới có quyền xóa thành viên.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Sự kiện hoặc thành viên không tồn tại trong sự kiện.",
        },
    },
)
def remove_member(
    user_id: int,
    event: Event = Depends(require_event_owner),
    db: Session = Depends(get_db),
):
    event_service.remove_member(db, event, user_id)
