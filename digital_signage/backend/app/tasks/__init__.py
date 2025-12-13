"""
Zadania w tle (Celery tasks)
"""
from app.tasks.processing import (
    process_image_task,
    process_pdf_task,
    process_excel_task,
    process_video_task
)
from app.tasks.monitoring import check_displays_offline

__all__ = [
    "process_image_task",
    "process_pdf_task",
    "process_excel_task",
    "process_video_task",
    "check_displays_offline",
]
