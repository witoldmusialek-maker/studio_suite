"""
Endpointy API dla treści
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.models.content import Content
from app.models.user import User
from app.api.deps import get_current_user, get_current_admin
from app.schemas.content import (
    ContentResponse,
    ContentListResponse,
    ContentUpdate,
    ProcessingJobResponse
)
from app.services.content_service import (
    save_uploaded_file,
    create_content_record,
    create_processing_job
)
from app.utils.file_utils import get_file_type, get_file_size_mb

router = APIRouter(prefix="/content", tags=["content"])


@router.post("/upload", response_model=ContentResponse, status_code=status.HTTP_201_CREATED)
async def upload_content(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Upload treści (tylko admin)"""
    # Walidacja typu pliku
    file_type = get_file_type(file.content_type)
    if file_type is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Nieobsługiwany typ pliku: {file.content_type}"
        )
    
    # Odczyt pliku do obliczenia rozmiaru
    content_bytes = await file.read()
    file_size_mb = len(content_bytes) / (1024 * 1024)
    
    # Utworzenie rekordu w bazie (bez file_path na razie)
    db_content = create_content_record(
        db=db,
        original_filename=file.filename,
        file_type=file_type,
        file_path="",  # Zostanie zaktualizowane
        file_size_mb=round(file_size_mb, 2),
        uploaded_by=current_user.id
    )
    
    # Zapis pliku
    from io import BytesIO
    file.file = BytesIO(content_bytes)
    file_path, error = save_uploaded_file(file, db_content.id, db)
        
        if error:
            # Usunięcie rekordu z bazy jeśli błąd
            db.delete(db_content)
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )
        
        # Aktualizacja file_path
        db_content.file_path = file_path
        db.commit()
        db.refresh(db_content)
        
        # Utworzenie zadania przetwarzania
        job = None
        if file_type == "video":
            job = create_processing_job(db, db_content.id, "video_transcode")
            from app.tasks.processing import process_video_task
            process_video_task.delay(db_content.id, job.id)
        elif file_type == "pdf":
            job = create_processing_job(db, db_content.id, "pdf_convert")
            from app.tasks.processing import process_pdf_task
            process_pdf_task.delay(db_content.id, job.id)
        elif file_type == "excel":
            job = create_processing_job(db, db_content.id, "excel_process")
            from app.tasks.processing import process_excel_task
            process_excel_task.delay(db_content.id, job.id)
        elif file_type == "image":
            job = create_processing_job(db, db_content.id, "image_process")
            from app.tasks.processing import process_image_task
            process_image_task.delay(db_content.id, job.id)
        
        return db_content


@router.get("/", response_model=ContentListResponse)
async def get_contents(
    skip: int = 0,
    limit: int = 100,
    type_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Pobranie listy treści (admin i operator)"""
    query = db.query(Content)
    
    if type_filter:
        query = query.filter(Content.type == type_filter)
    
    total = query.count()
    contents = query.order_by(Content.created_at.desc()).offset(skip).limit(limit).all()
    
    return ContentListResponse(
        items=contents,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{content_id}", response_model=ContentResponse)
async def get_content(
    content_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Pobranie szczegółów treści"""
    content = db.query(Content).filter(Content.id == content_id).first()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )
    return content


@router.put("/{content_id}", response_model=ContentResponse)
async def update_content(
    content_id: int,
    content_data: ContentUpdate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Aktualizacja treści (tylko admin)"""
    content = db.query(Content).filter(Content.id == content_id).first()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )
    
    update_data = content_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(content, field, value)
    
    db.commit()
    db.refresh(content)
    return content


@router.delete("/{content_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_content(
    content_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Usunięcie treści (tylko admin)"""
    content = db.query(Content).filter(Content.id == content_id).first()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )
    
    # Usunięcie pliku z dysku
    import os
    if os.path.exists(content.file_path):
        os.remove(content.file_path)
    if content.thumbnail_path and os.path.exists(content.thumbnail_path):
        os.remove(content.thumbnail_path)
    
    db.delete(content)
    db.commit()
    return None


@router.get("/{content_id}/processing-jobs", response_model=List[ProcessingJobResponse])
async def get_processing_jobs(
    content_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Pobranie zadań przetwarzania dla treści"""
    from app.models.processing_job import ProcessingJob
    
    jobs = db.query(ProcessingJob).filter(
        ProcessingJob.content_id == content_id
    ).order_by(ProcessingJob.created_at.desc()).all()
    
    return jobs

