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
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str | None) -> str | None:
        if v is not None:
            stripped = v.strip()
            if not stripped:
                raise ValueError("Tên sự kiện không được để trống")
            return stripped
        return v

class EventTaskReplace(BaseModel):         
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Tên sự kiện không được để trống")
        return stripped


class EventTaskResponse(EventTaskBase):
    id: int = Field(..., description="Mã định danh duy nhất của công việc", example=1)
    event_id: int = Field(..., description="ID sự kiện chứa công việc này", example=1)
    assignee_id: int | None = Field(None, description="ID người được phân công (null nếu chưa giao)", example=2)
    status: TaskStatus = Field(..., description="Trạng thái tiến độ công việc", example=TaskStatus.TODO)
    created_at: datetime = Field(..., description="Thời gian tạo công việc")

    model_config = ConfigDict(from_attributes=True)
