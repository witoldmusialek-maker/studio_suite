"""
Model alertów
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class Alert(Base):
    """Model alertu"""
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    display_id = Column(Integer, ForeignKey("displays.id", ondelete="CASCADE"), nullable=False)
    alert_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False, index=True)
    message = Column(Text, nullable=False)
    resolved = Column(Boolean, default=False, nullable=False, index=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    display = relationship("Display", back_populates="alerts", passive_deletes=True)
    resolver = relationship("User", foreign_keys=[resolved_by])

    def __repr__(self):
        return f"<Alert(id={self.id}, display_id={self.display_id}, type={self.alert_type}, severity={self.severity})>"



