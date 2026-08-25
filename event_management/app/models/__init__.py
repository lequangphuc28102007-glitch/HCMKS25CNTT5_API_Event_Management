"""
Import tất cả model ở đây để khi Base.metadata.create_all() chạy,
SQLAlchemy nhận biết đủ toàn bộ bảng cần tạo.
"""
from app.models.user import User  # noqa: F401
from app.models.event import Event, EventStaff  # noqa: F401
from app.models.event_task import EventTask  # noqa: F401
