from typing import TYPE_CHECKING, Optional
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import ForeignKey, String, Text, Enum, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.db.database import Base
import enum
import uuid
if TYPE_CHECKING:
    from app.models.user import User
    from app.models.event_task import EventTask
    from app.models.event_staff import EventStaff


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str] = mapped_column(Text, default=None)
    location: Mapped[str] = mapped_column(String(255), default=None)
    starts_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    owner: Mapped["User"] = relationship(back_populates="events")
    tasks: Mapped[list["EventTask"]] = relationship(back_populates="event", cascade="all, delete-orphan")
    staff: Mapped[list["EventStaff"]] = relationship(back_populates="event", cascade="all, delete-orphan")



