"""
Schematy treści
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any


class ContentBase(BaseModel):
    """Podstawowy schemat treści"""
    filename: str
    type: str


class ContentCreate(BaseModel):
    """Schemat tworzenia treści (z uploadu)"""
    original_filename: str
    type: str
    file_size_mb: Optional[float] = None


class ContentUpdate(BaseModel):
    """Schemat aktualizacji treści"""
    filename: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ContentResponse(ContentBase):
    """Schemat odpowiedzi treści"""
    id: int
    original_filename: str
    file_path: str
    thumbnail_path: Optional[str] = None
    video_processed: bool = False
    video_format: Optional[str] = None
    file_size_mb: Optional[float] = None
    duration_seconds: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    uploaded_by: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ContentListResponse(BaseModel):
    """Schemat listy treści"""
    items: list[ContentResponse]
    total: int
    skip: int
    limit: int


class ProcessingJobResponse(BaseModel):
    """Schemat zadania przetwarzania"""
    id: int
    content_id: int
    job_type: str
    status: str
    progress: int
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

