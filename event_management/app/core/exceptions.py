
import logging
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("event_management")


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


class ConflictException(AppException):
    def __init__(self, message: str = "Tài nguyên đã tồn tại hoặc xảy ra xung đột"):
        super().__init__(status.HTTP_409_CONFLICT, message)


class InternalServerErrorException(AppException):
    def __init__(self, message: str = "Đã xảy ra lỗi máy chủ nội bộ. Vui lòng liên hệ quản trị viên."):
        super().__init__(status.HTTP_500_INTERNAL_SERVER_ERROR, message)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": True, "message": exc.message},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        def _sanitize(errors: list) -> list:
            result = []
            for err in errors:
                sanitized = {k: v for k, v in err.items() if k != "ctx"}
                if "ctx" in err:
                    sanitized["ctx"] = {
                        ck: str(cv) if not isinstance(cv, (str, int, float, bool, type(None))) else cv
                        for ck, cv in err["ctx"].items()
                    }
                result.append(sanitized)
            return result

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": True,
                "message": "Dữ liệu gửi lên không hợp lệ",
                "detail": _sanitize(exc.errors()),
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": True,
                "message": exc.detail if isinstance(exc.detail, str) else "Lỗi yêu cầu HTTP",
            },
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled server error on {request.method} {request.url.path}: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": True,
                "message": "Đã xảy ra lỗi máy chủ nội bộ. Vui lòng thử lại sau.",
            },
        )
