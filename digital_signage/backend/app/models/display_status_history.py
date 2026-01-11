"""
Model historii statusów wyświetlaczy
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func

from app.database import Base


class DisplayStatusHistory(Base):
    """Model historii statusów wyświetlacza"""
    __tablename__ = "display_status_history"

    id = Column(Integer, primary_key=True, index=True)
    display_id = Column(Integer, ForeignKey("displays.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(20), nullable=False)
    last_seen = Column(DateTime(timezone=True), nullable=True)
    connection_lost_at = Column(DateTime(timezone=True), nullable=True)
    connection_restored_at = Column(DateTime(timezone=True), nullable=True)
    duration_offline_seconds = Column(Integer, nullable=True)
    error_message = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    def __repr__(self):
        return f"<DisplayStatusHistory(id={self.id}, display_id={self.display_id}, status={self.status})>"



