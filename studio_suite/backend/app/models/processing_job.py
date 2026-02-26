"""
Model zadania przetwarzania
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.sql import func

from app.database import Base


class ProcessingJob(Base):
    """Model zadania przetwarzania treści"""
    __tablename__ = "processing_jobs"

    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(Integer, ForeignKey("content.id", ondelete="CASCADE"), nullable=False)
    job_type = Column(String(50), nullable=False)
    status = Column(String(20), default="pending", nullable=False, index=True)
    progress = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<ProcessingJob(id={self.id}, content_id={self.content_id}, status={self.status})>"

