"""
Sound library for bell engine.
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func

from app.database import Base


class BellSound(Base):
    __tablename__ = "bell_sounds"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False, unique=True, index=True)
    file_path = Column(String(500), nullable=False)
    mime_type = Column(String(120), nullable=True)
    size_bytes = Column(Integer, nullable=True)
    active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
