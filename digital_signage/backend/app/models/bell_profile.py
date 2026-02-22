"""
Bell schedule profiles and date overrides.
"""
from sqlalchemy import Column, Integer, String, DateTime, Date, Boolean, ForeignKey
from sqlalchemy.sql import func

from app.database import Base


class BellProfile(Base):
    __tablename__ = "bell_profiles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False, unique=True)
    month = Column(Integer, nullable=True)  # 1-12, optional
    is_default = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class BellProfileOverride(Base):
    __tablename__ = "bell_profile_overrides"

    id = Column(Integer, primary_key=True, index=True)
    day = Column(Date, nullable=False, unique=True, index=True)
    profile_id = Column(Integer, ForeignKey("bell_profiles.id", ondelete="CASCADE"), nullable=False)
    reason = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class BellScheduleProfile(Base):
    __tablename__ = "bell_schedule_profiles"

    id = Column(Integer, primary_key=True, index=True)
    bell_schedule_id = Column(Integer, ForeignKey("bell_schedules.id", ondelete="CASCADE"), nullable=False, index=True)
    profile_id = Column(Integer, ForeignKey("bell_profiles.id", ondelete="CASCADE"), nullable=False, index=True)


class BellProfilePlaceholder(Base):
    __tablename__ = "bell_profile_placeholders"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("bell_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    placeholder_key = Column(String(80), nullable=False, index=True)
    sound_id = Column(Integer, ForeignKey("bell_sounds.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
