from typing import TYPE_CHECKING, Optional
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import ForeignKey, String, Text, Enum, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.db.database import Base
import enum
import uuid

if TYPE_CHECKING:
    from event_management.app.models.user import User
    from event_management.app.models.event import Event

class StaffRole(enum.Enum):
    OWNER = "OWNER"
    MEMBER = "MEMBER"

class EventStaff(Base):
    __tablename__ = "event_staff"

    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role: Mapped[StaffRole] = mapped_column(Enum(StaffRole, name="staff_role"), nullable=False)
    joined_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    event: Mapped["Event"] = relationship("Event", back_populates="staff")
    user: Mapped["User"] = relationship("User", back_populates="events")