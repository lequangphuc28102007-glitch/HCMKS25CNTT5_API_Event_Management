from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.event_task import TaskPriority, TaskStatus


class EventTaskBase(BaseModel):
    title: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Tiêu đề công việc cần thực hiện",
        example="Chuẩn bị backdrop sân khấu chính",
    )
    description: str | None = Field(
        default=None,
        description="Mô tả chi tiết yêu cầu công việc",
        example="Thiết kế và in ấn backdrop sân khấu chính kích thước 6x3m.",
    )
    due_date: datetime | None = Field(
        default=None,
        description="Hạn chót hoàn thành công việc (ISO 8601)",
        example="2026-09-01T17:00:00",
    )
    priority: TaskPriority = Field(
        default=TaskPriority.MEDIUM,
        description="Độ ưu tiên của công việc (LOW, MEDIUM, HIGH)",
        example=TaskPriority.HIGH,
    )

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Tiêu đề công việc không được để trống hoặc chỉ chứa khoảng trắng")
        return stripped


class EventTaskCreate(EventTaskBase):
    assignee_id: int | None = Field(
        default=None,
        description="ID thành viên sự kiện được phân công phụ trách công việc",
        example=2,
    )


class EventTaskUpdate(BaseModel):
    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Tiêu đề mới của công việc",
        example="Hoàn thiện backdrop sân khấu chính",
    )
    description: str | None = Field(
        default=None,
        description="Mô tả cập nhật của công việc",
        example="Đã in ấn xong, đang tiến hành căng khung sân khấu.",
    )
    due_date: datetime | None = Field(
        default=None,
        description="Hạn chót mới",
        example="2026-09-02T12:00:00",
    )
    priority: TaskPriority | None = Field(
        default=None,
        description="Độ ưu tiên mới (LOW, MEDIUM, HIGH)",
        example=TaskPriority.HIGH,
    )
    status: TaskStatus | None = Field(
        default=None,
        description="Trạng thái tiến độ công việc (TODO, IN_PROGRESS, DONE)",
        example=TaskStatus.IN_PROGRESS,
    )
    assignee_id: int | None = Field(
        default=None,
        description="ID thành viên được phân công lại (truyền null để bỏ phân công)",
        example=2,
    )

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str | None) -> str | None:
        if v is not None:
            stripped = v.strip()
            if not stripped:
                raise ValueError("Tiêu đề công việc không được để trống hoặc chỉ chứa khoảng trắng")
            return stripped
        return v


class EventTaskResponse(EventTaskBase):
    id: int = Field(..., description="Mã định danh duy nhất của công việc", example=1)
    event_id: int = Field(..., description="ID sự kiện chứa công việc này", example=1)
    assignee_id: int | None = Field(None, description="ID người được phân công (null nếu chưa giao)", example=2)
    status: TaskStatus = Field(..., description="Trạng thái tiến độ công việc", example=TaskStatus.TODO)
    created_at: datetime = Field(..., description="Thời gian tạo công việc")

    model_config = ConfigDict(from_attributes=True)
