"""
Model treści
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Numeric, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class Content(Base):
    """Model treści"""
    __tablename__ = "content"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    type = Column(String(20), nullable=False, index=True)
    file_path = Column(String(500), nullable=False)
    thumbnail_path = Column(String(500), nullable=True)
    video_processed = Column(Boolean, default=False)
    video_format = Column(String(10), nullable=True)
    file_size_mb = Column(Numeric(10, 2), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    content_metadata = Column(JSON, nullable=True)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Content(id={self.id}, filename={self.filename}, type={self.type})>"

