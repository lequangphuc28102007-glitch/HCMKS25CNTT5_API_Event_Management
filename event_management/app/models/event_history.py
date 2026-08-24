from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime
from app.db.database import Base


class EventHistory(Base):
    __tablename__ = "event_history"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String, nullable=False) 
    timestamp = Column(DateTime, default=datetime.utcnow)
    detail = Column(String)  
