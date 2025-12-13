"""
Model harmonogramu
"""
from sqlalchemy import Column, Integer, String, DateTime, Time, Date, Boolean, ForeignKey, ARRAY
from sqlalchemy.sql import func

from app.database import Base


class Schedule(Base):
    """Model harmonogramu wyświetlania treści"""
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    content_id = Column(Integer, ForeignKey("content.id", ondelete="CASCADE"), nullable=False)
    display_id = Column(Integer, ForeignKey("displays.id", ondelete="CASCADE"), nullable=True)
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"), nullable=True)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    days_of_week = Column(ARRAY(Integer), nullable=True)  # [1,2,3,4,5] = pon-pt
    priority = Column(Integer, default=0)
    display_duration_seconds = Column(Integer, nullable=True)
    active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<Schedule(id={self.id}, name={self.name}, active={self.active})>"

