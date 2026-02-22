"""
Break music schedules and playlist tracks.
"""
from sqlalchemy import Column, Integer, String, DateTime, Time, Date, Boolean, ARRAY, ForeignKey
from sqlalchemy.sql import func

from app.database import Base


class BellMusicSchedule(Base):
    __tablename__ = "bell_music_schedules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    start_time = Column(Time, nullable=False, index=True)
    end_time = Column(Time, nullable=False, index=True)
    days_of_week = Column(ARRAY(Integer), nullable=True)  # [1..7], 1=Mon
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    display_ids = Column(ARRAY(Integer), nullable=True)
    profile_ids = Column(ARRAY(Integer), nullable=True)
    volume = Column(Integer, nullable=False, default=50)
    priority = Column(Integer, nullable=False, default=0)
    active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class BellMusicTrack(Base):
    __tablename__ = "bell_music_tracks"

    id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(Integer, ForeignKey("bell_music_schedules.id", ondelete="CASCADE"), nullable=False, index=True)
    file_path = Column(String(500), nullable=False)
    title = Column(String(255), nullable=True)
    sort_order = Column(Integer, nullable=False, default=0)
    active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
