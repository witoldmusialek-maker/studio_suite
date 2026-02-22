"""
Model harmonogramu dzwonków szkolnych
"""
from sqlalchemy import Column, Integer, String, DateTime, Time, Date, Boolean, ForeignKey, ARRAY
from sqlalchemy.sql import func

from app.database import Base


class BellSchedule(Base):
    """Model harmonogramu dzwonka"""
    __tablename__ = "bell_schedules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    bell_time = Column(Time, nullable=False, index=True)
    event_type = Column(String(20), default='lesson')  # 'lesson' = na lekcję, 'break' = na przerwę
    days_of_week = Column(ARRAY(Integer), nullable=True)  # [1,2,3,4,5] = pon-pt
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    sound_file_path = Column(String(500), nullable=True)
    volume = Column(Integer, default=50)
    play_on_displays = Column(Boolean, default=True)
    display_ids = Column(ARRAY(Integer), nullable=True)  # Puste = wszystkie
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True)  # Grupa docelowa
    playlist_id = Column(Integer, ForeignKey("bell_music_schedules.id"), nullable=True)  # Playlista na przerwę
    active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<BellSchedule(id={self.id}, name={self.name}, bell_time={self.bell_time})>"



