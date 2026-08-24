from datetime import datetime
from typing import TYPE_CHECKING, List
import enum

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship


from app.db.database import Base
if TYPE_CHECKING:
    from app.models.event import Event
    from app.models.event_task import EventTask
    from app.models.event_staff import EventStaff

class UserStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"

class UserRole(str, enum.Enum):
    USER = "USER"
    ADMIN = "ADMIN"

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index= True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable= False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(String(20), default="USER")
    is_active: Mapped[UserStatus] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)

    events: Mapped[List["Event"]] = relationship(back_populates="owner")
    tasks: Mapped[List["EventTask"]] = relationship(back_populates="assignee")
    staff_memberships: Mapped[List["EventStaff"]] = relationship(back_populates="user")
