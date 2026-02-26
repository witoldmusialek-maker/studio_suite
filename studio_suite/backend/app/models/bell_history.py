"""
Model historii odtworzeń dzwonków
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func

from app.database import Base


class BellHistory(Base):
    """Model historii odtworzenia dzwonka"""
    __tablename__ = "bell_history"

    id = Column(Integer, primary_key=True, index=True)
    bell_schedule_id = Column(Integer, ForeignKey("bell_schedules.id", ondelete="CASCADE"), nullable=False, index=True)
    played_at = Column(DateTime(timezone=True), nullable=False, index=True)
    status = Column(String(20), default="success", nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<BellHistory(id={self.id}, bell_schedule_id={self.bell_schedule_id}, status={self.status})>"



