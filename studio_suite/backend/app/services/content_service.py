"""
Serwis do zarządzania treścią
"""
import os
import shutil
from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import UploadFile

from app.models.content import Content
from app.models.processing_job import ProcessingJob
from app.config import settings
from app.utils.file_utils import (
    get_file_type,
    validate_file_type,
    get_file_size_mb,
    ensure_directory_exists
)


def save_uploaded_file(
    file: UploadFile,
    content_id: int,
    db: Session
) -> tuple[str, Optional[str]]:
    """
    Zapisanie przesłanego pliku
    Zwraca (file_path, error_message)
    """
    # Walidacja typu pliku
    is_valid, error = validate_file_type(file.content_type, file.filename)
    if not is_valid:
        return None, error
    
    # Określenie typu i katalogu
    file_type = get_file_type(file.content_type)
    if file_type == "video":
        # Video będzie przetworzone później, więc zapisujemy do processed
        save_dir = settings.CONTENT_PROCESSED_DIR
    else:
        save_dir = settings.CONTENT_ORIGINAL_DIR
    
    ensure_directory_exists(save_dir)
    
    # Generowanie nazwy pliku
    ext = Path(file.filename).suffix
    filename = f"{content_id}_{file.filename}"
    file_path = os.path.join(save_dir, filename)
    
    # Zapis pliku
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return file_path, None
    except Exception as e:
        return None, str(e)


def create_content_record(
    db: Session,
    original_filename: str,
    file_type: str,
    file_path: str,
    file_size_mb: float,
    uploaded_by: int
) -> Content:
    """Utworzenie rekordu treści w bazie danych"""
    db_content = Content(
        filename=original_filename,
        original_filename=original_filename,
        type=file_type,
        file_path=file_path,
        file_size_mb=file_size_mb,
        uploaded_by=uploaded_by
    )
    db.add(db_content)
    db.commit()
    db.refresh(db_content)
    return db_content


def create_processing_job(
    db: Session,
    content_id: int,
    job_type: str
) -> ProcessingJob:
    """Utworzenie zadania przetwarzania"""
    db_job = ProcessingJob(
        content_id=content_id,
        job_type=job_type,
        status="pending"
    )
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job


def update_processing_job(
    db: Session,
    job_id: int,
    status: str,
    progress: Optional[int] = None,
    error_message: Optional[str] = None
):
    """Aktualizacja zadania przetwarzania"""
    job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
    if job:
        job.status = status
        if progress is not None:
            job.progress = progress
        if error_message:
            job.error_message = error_message
        db.commit()

