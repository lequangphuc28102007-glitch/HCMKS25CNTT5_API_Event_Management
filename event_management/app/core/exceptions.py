
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class AppException(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message


class NotFoundException(AppException):
    def __init__(self, message: str = "Không tìm thấy dữ liệu"):
        super().__init__(status.HTTP_404_NOT_FOUND, message)


class BadRequestException(AppException):
    def __init__(self, message: str = "Dữ liệu không hợp lệ"):
        super().__init__(status.HTTP_400_BAD_REQUEST, message)


class ForbiddenException(AppException):
    def __init__(self, message: str = "Bạn không có quyền thực hiện thao tác này"):
        super().__init__(status.HTTP_403_FORBIDDEN, message)


class UnauthorizedException(AppException):
    def __init__(self, message: str = "Chưa xác thực hoặc token không hợp lệ"):
        super().__init__(status.HTTP_401_UNAUTHORIZED, message)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": True, "message": exc.message},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"error": True, "message": "Dữ liệu gửi lên không hợp lệ", "detail": exc.errors()},
        )
