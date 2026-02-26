"""
Narzędzia do obsługi plików
"""
import os
import hashlib
from pathlib import Path
from typing import Optional, Tuple
from fastapi import UploadFile


ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/jpg"}
ALLOWED_PDF_TYPES = {"application/pdf"}
ALLOWED_EXCEL_TYPES = {
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel"
}
ALLOWED_VIDEO_TYPES = {"video/mpeg", "video/mp4", "video/x-msvideo"}

ALLOWED_TYPES = ALLOWED_IMAGE_TYPES | ALLOWED_PDF_TYPES | ALLOWED_EXCEL_TYPES | ALLOWED_VIDEO_TYPES


def get_file_type(content_type: str) -> Optional[str]:
    """Określenie typu pliku na podstawie content_type"""
    if content_type in ALLOWED_IMAGE_TYPES:
        return "image"
    elif content_type in ALLOWED_PDF_TYPES:
        return "pdf"
    elif content_type in ALLOWED_EXCEL_TYPES:
        return "excel"
    elif content_type in ALLOWED_VIDEO_TYPES:
        return "video"
    return None


def get_file_extension(filename: str) -> str:
    """Pobranie rozszerzenia pliku"""
    return Path(filename).suffix.lower()


def validate_file_type(content_type: str, filename: str) -> Tuple[bool, Optional[str]]:
    """
    Walidacja typu pliku
    Zwraca (is_valid, error_message)
    """
    file_type = get_file_type(content_type)
    if file_type is None:
        return False, f"Nieobsługiwany typ pliku: {content_type}"
    
    # Dodatkowa walidacja przez rozszerzenie
    ext = get_file_extension(filename)
    if file_type == "image" and ext not in [".jpg", ".jpeg", ".png", ".gif"]:
        return False, f"Nieprawidłowe rozszerzenie dla obrazu: {ext}"
    elif file_type == "pdf" and ext != ".pdf":
        return False, f"Nieprawidłowe rozszerzenie dla PDF: {ext}"
    elif file_type == "excel" and ext not in [".xlsx", ".xls"]:
        return False, f"Nieprawidłowe rozszerzenie dla Excel: {ext}"
    elif file_type == "video" and ext not in [".mpg", ".mpeg", ".mp4", ".avi"]:
        return False, f"Nieprawidłowe rozszerzenie dla video: {ext}"
    
    return True, None


def calculate_file_hash(file_path: str) -> str:
    """Obliczenie hash pliku (SHA256)"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def get_file_size_mb(file_path: str) -> float:
    """Pobranie rozmiaru pliku w MB"""
    size_bytes = os.path.getsize(file_path)
    return round(size_bytes / (1024 * 1024), 2)


def ensure_directory_exists(directory: str):
    """Utworzenie katalogu jeśli nie istnieje"""
    Path(directory).mkdir(parents=True, exist_ok=True)

