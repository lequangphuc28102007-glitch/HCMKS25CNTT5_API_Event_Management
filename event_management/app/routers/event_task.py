from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.permissions import require_event_member
from app.models.event import Event
from app.models.event_task import TaskPriority, TaskStatus
from app.models.user import User
from app.schemas.common import ErrorResponse, PaginatedResponse, ValidationErrorResponse
from app.schemas.event_task import EventTaskCreate, EventTaskResponse, EventTaskUpdate
from app.services import event_task_service

router = APIRouter(tags=["Event Tasks"])


@router.post(
    "/events/{event_id}/event-tasks",
    response_model=EventTaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo công việc mới trong sự kiện",
    description=(
        "Thành viên của sự kiện tạo một công việc mới.\n\n"
        "**Quy tắc nghiệp vụ & Phân quyền:**\n"
        "- Chỉ thành viên (`OWNER` hoặc `MEMBER`) của sự kiện mới được tạo công việc.\n"
        "- `title` là bắt buộc, không được để trống hoặc chỉ chứa khoảng trắng.\n"
        "- `priority`: Mặc định là `MEDIUM` (hỗ trợ `LOW`, `MEDIUM`, `HIGH`).\n"
        "- `status`: Mặc định là `TODO`.\n"
        "- `assignee_id`: Tùy chọn. Nếu gán người làm, người đó **bắt buộc phải là thành viên** của sự kiện."
    ),
    responses={
        status.HTTP_201_CREATED: {
            "model": EventTaskResponse,
            "description": "Tạo công việc thành công.",
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": "Người được phân công không phải là thành viên của sự kiện hoặc tài khoản bị khóa.",
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
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "model": ValidationErrorResponse,
            "description": "Dữ liệu gửi lên sai định dạng (ví dụ: priority sai enum, title để trống).",
        },
    },
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
    status_code=status.HTTP_200_OK,
    summary="Danh sách công việc trong sự kiện (Lọc, Sắp xếp, Phân trang)",
    description=(
        "Lấy danh sách các công việc thuộc sự kiện kèm khả năng lọc nâng cao, tìm kiếm và phân trang.\n\n"
        "**Phân quyền:**\n"
        "- Chỉ thành viên (`OWNER` hoặc `MEMBER`) của sự kiện mới được xem.\n\n"
        "**Khả năng lọc & Sắp xếp:**\n"
        "- `status`: Lọc theo trạng thái (`TODO`, `IN_PROGRESS`, `DONE`).\n"
        "- `priority`: Lọc theo độ ưu tiên (`LOW`, `MEDIUM`, `HIGH`).\n"
        "- `assignee_id`: Lọc theo ID người phụ trách.\n"
        "- `search`: Tìm kiếm theo tiêu đề công việc (không phân biệt hoa thường).\n"
        "- `sort_by`: Sắp xếp theo `created_at` (ngày tạo) hoặc `due_date` (hạn chót).\n"
        "- `sort_order`: `asc` (tăng dần) hoặc `desc` (giảm dần).\n"
        "- `page` & `size`: Phân trang kết quả (mặc định page 1, size 10)."
    ),
    responses={
        status.HTTP_200_OK: {
            "model": PaginatedResponse[EventTaskResponse],
            "description": "Danh sách công việc phân trang thành công.",
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
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "model": ValidationErrorResponse,
            "description": "Tham số lọc hoặc phân trang không hợp lệ.",
        },
    },
)
def list_tasks(
    event: Event = Depends(require_event_member),
    status_filter: TaskStatus | None = Query(
        default=None,
        alias="status",
        description="Lọc theo trạng thái công việc (TODO, IN_PROGRESS, DONE)",
    ),
    priority: TaskPriority | None = Query(
        default=None,
        description="Lọc theo độ ưu tiên (LOW, MEDIUM, HIGH)",
    ),
    assignee_id: int | None = Query(
        default=None,
        description="Lọc theo ID người được phân công",
    ),
    search: str | None = Query(
        default=None,
        description="Tìm kiếm theo tiêu đề công việc (không phân biệt hoa thường)",
    ),
    sort_by: str = Query(
        default="created_at",
        pattern="^(?i)(created_at|due_date)$",
        description="Trường sắp xếp: created_at hoặc due_date",
    ),
    sort_order: str = Query(
        default="desc",
        pattern="^(?i)(asc|desc)$",
        description="Thứ tự sắp xếp: asc hoặc desc",
    ),
    page: int = Query(
        default=1,
        ge=1,
        description="Số thứ tự trang (bắt đầu từ 1)",
    ),
    size: int = Query(
        default=10,
        ge=1,
        le=100,
        description="Số lượng mục trên mỗi trang (từ 1 đến 100)",
    ),
    db: Session = Depends(get_db),
):
    items, total = event_task_service.list_tasks(
        db, event.id, status_filter, priority, assignee_id, search, sort_by, sort_order, page, size
    )
    return PaginatedResponse(total=total, page=page, size=size, items=items)


@router.get(
    "/event-tasks/{task_id}",
    response_model=EventTaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Chi tiết công việc sự kiện",
    description=(
        "Lấy thông tin chi tiết của một công việc cụ thể theo `task_id`.\n\n"
        "**Phân quyền:**\n"
        "- Người dùng phải là thành viên (`OWNER` hoặc `MEMBER`) của sự kiện chứa công việc này."
    ),
    responses={
        status.HTTP_200_OK: {
            "model": EventTaskResponse,
            "description": "Thông tin chi tiết công việc.",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "model": ErrorResponse,
            "description": "Chưa đăng nhập hoặc token không hợp lệ.",
        },
        status.HTTP_403_FORBIDDEN: {
            "model": ErrorResponse,
            "description": "Bạn không phải thành viên của sự kiện chứa công việc này.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Công việc sự kiện không tồn tại.",
        },
    },
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
    status_code=status.HTTP_200_OK,
    summary="Cập nhật công việc sự kiện (PATCH)",
    description=(
        "Cập nhật từng phần thông tin công việc (tiêu đề, mô tả, hạn chót, độ ưu tiên, trạng thái, người làm).\n\n"
        "**Phân quyền:**\n"
        "- Chỉ `OWNER` của sự kiện hoặc `Assignee` (người được giao công việc đó) mới có quyền chỉnh sửa.\n"
        "- Nếu thay đổi người phụ trách (`assignee_id`), người mới phải là thành viên của sự kiện."
    ),
    responses={
        status.HTTP_200_OK: {
            "model": EventTaskResponse,
            "description": "Cập nhật công việc thành công.",
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": "Người được phân công không phải là thành viên sự kiện.",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "model": ErrorResponse,
            "description": "Chưa đăng nhập hoặc token không hợp lệ.",
        },
        status.HTTP_403_FORBIDDEN: {
            "model": ErrorResponse,
            "description": "Bạn không có quyền sửa công việc này.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Công việc sự kiện không tồn tại.",
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "model": ValidationErrorResponse,
            "description": "Dữ liệu cập nhật sai định dạng.",
        },
    },
)
@router.put(
    "/event-tasks/{task_id}",
    response_model=EventTaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Cập nhật công việc sự kiện (PUT)",
    description=(
        "Cập nhật thông tin công việc (tiêu đề, mô tả, hạn chót, độ ưu tiên, trạng thái, người làm).\n\n"
        "**Phân quyền:**\n"
        "- Chỉ `OWNER` của sự kiện hoặc `Assignee` mới có quyền chỉnh sửa."
    ),
    responses={
        status.HTTP_200_OK: {
            "model": EventTaskResponse,
            "description": "Cập nhật công việc thành công.",
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": "Người được phân công không phải là thành viên sự kiện.",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "model": ErrorResponse,
            "description": "Chưa đăng nhập hoặc token không hợp lệ.",
        },
        status.HTTP_403_FORBIDDEN: {
            "model": ErrorResponse,
            "description": "Bạn không có quyền sửa công việc này.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Công việc sự kiện không tồn tại.",
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "model": ValidationErrorResponse,
            "description": "Dữ liệu cập nhật sai định dạng.",
        },
    },
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
    description=(
        "Xóa một công việc trong sự kiện.\n\n"
        "**Phân quyền:**\n"
        "- Chỉ `OWNER` của sự kiện hoặc `Assignee` (người được giao công việc) mới có quyền xóa."
    ),
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": "Xóa công việc thành công (không có nội dung trả về).",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "model": ErrorResponse,
            "description": "Chưa đăng nhập hoặc token không hợp lệ.",
        },
        status.HTTP_403_FORBIDDEN: {
            "model": ErrorResponse,
            "description": "Bạn không có quyền xóa công việc này.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Công việc sự kiện không tồn tại.",
        },
    },
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
