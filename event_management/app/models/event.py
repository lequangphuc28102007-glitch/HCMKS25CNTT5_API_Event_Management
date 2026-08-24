from datetime import datetime
from typing import TYPE_CHECKING, List
from sqlalchemy import ForeignKey, String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.db.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.event_task import EventTask
    from app.models.event_staff import EventStaff


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    location: Mapped[str] = mapped_column(String(255), nullable=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    is_deleted:Mapped[bool] = mapped_column(default=False)
    deleted_at: Mapped[datetime] = mapped_column(nullable=True)

    owner: Mapped["User"] = relationship(back_populates="events")
    tasks: Mapped[List["EventTask"]] = relationship(back_populates="event", cascade="all, delete-orphan")
    staff: Mapped[List["EventStaff"]] = relationship(back_populates="event", cascade="all, delete-orphan")



