"""
Runtime control and calendar overrides for bells.
"""
from sqlalchemy import Column, Integer, String, DateTime, Date, Boolean
from sqlalchemy.sql import func

from app.database import Base


class BellRuntimeControl(Base):
    """Global runtime flags for bell engine."""
    __tablename__ = "bell_runtime_control"

    id = Column(Integer, primary_key=True, index=True)
    bells_enabled = Column(Boolean, nullable=False, default=True)
    pause_until = Column(DateTime(timezone=True), nullable=True)
    pause_reason = Column(String(255), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class BellCalendarOverride(Base):
    """Date-based temporary override for bells or day-type templates."""
    __tablename__ = "bell_calendar_overrides"

    id = Column(Integer, primary_key=True, index=True)
    day = Column(Date, nullable=True, index=True)  # None = szablon typu dnia
    bells_enabled = Column(Boolean, nullable=False, default=True)
    reason = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
