from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    total: int = Field(..., description="Tổng số bản ghi thỏa mãn điều kiện lọc", example=25)
    page: int = Field(..., description="Số trang hiện tại (bắt đầu từ 1)", example=1)
    size: int = Field(..., description="Số lượng bản ghi trên một trang", example=10)
    items: list[T] = Field(..., description="Danh sách dữ liệu trong trang hiện tại")


class HealthResponse(BaseModel):
    status: str = Field("ok", description="Trạng thái hoạt động của dịch vụ", example="ok")


class ErrorResponse(BaseModel):
    error: bool = Field(True, description="Đánh dấu phản hồi có lỗi", example=True)
    message: str = Field(..., description="Thông báo lỗi chi tiết dễ hiểu", example="Dữ liệu không hợp lệ")


class ValidationErrorDetail(BaseModel):
    loc: list[str | int] = Field(..., description="Vị trí trường dữ liệu bị lỗi")
    msg: str = Field(..., description="Mô tả lỗi xác thực")
    type: str = Field(..., description="Mã kiểu lỗi xác thực")


class ValidationErrorResponse(BaseModel):
    error: bool = Field(True, description="Đánh dấu phản hồi có lỗi", example=True)
    message: str = Field("Dữ liệu gửi lên không hợp lệ", description="Thông điệp lỗi xác thực")
    detail: list[Any] | None = Field(default=None, description="Danh sách chi tiết các trường không hợp lệ")


RESPONSES_400_422 = {
    400: {"model": ErrorResponse, "description": "Yêu cầu không hợp lệ hoặc vi phạm logic nghiệp vụ"},
    422: {"model": ValidationErrorResponse, "description": "Dữ liệu đầu vào sai định dạng hoặc thiếu trường bắt buộc"},
}

RESPONSES_AUTH_PROTECTED = {
    401: {"model": ErrorResponse, "description": "Chưa xác thực hoặc JWT token không hợp lệ / hết hạn"},
    403: {"model": ErrorResponse, "description": "Không có quyền truy cập hoặc thực hiện thao tác trên tài nguyên này"},
}

RESPONSES_NOT_FOUND = {
    404: {"model": ErrorResponse, "description": "Không tìm thấy tài nguyên yêu cầu"},
}
