"""
Schematy tresci
"""
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class ContentBase(BaseModel):
    """Podstawowy schemat tresci"""
    filename: str
    type: str


class ContentCreate(BaseModel):
    """Schemat tworzenia tresci (z uploadu)"""
    original_filename: str
    type: str
    file_size_mb: Optional[float] = None


class ContentUpdate(BaseModel):
    """Schemat aktualizacji tresci"""
    filename: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ContentResponse(ContentBase):
    """Schemat odpowiedzi tresci"""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    name: str = Field(validation_alias="original_filename")
    original_filename: str
    file_path: str
    thumbnail_path: Optional[str] = None
    video_processed: bool = False
    video_format: Optional[str] = None
    file_size_mb: Optional[float] = None
    duration_seconds: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        validation_alias="content_metadata",
    )
    uploaded_by: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class ContentListResponse(BaseModel):
    """Schemat listy tresci"""
    items: list[ContentResponse]
    total: int
    skip: int
    limit: int


class ProcessingJobResponse(BaseModel):
    """Schemat zadania przetwarzania"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    content_id: int
    job_type: str
    status: str
    progress: int
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime