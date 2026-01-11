"""
Zarządzanie cache lokalnym
"""
import os
import hashlib
from pathlib import Path
from typing import Optional

import config


class CacheManager:
    """Zarządzanie cache lokalnym"""

    def __init__(self):
        self.cache_dir = Path(config.CACHE_DIR)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_file_path(self, content_id: int, filename: str) -> Path:
        """Pobranie ścieżki pliku w cache"""
        return self.cache_dir / f"{content_id}_{filename}"

    def file_exists(self, content_id: int, filename: str) -> bool:
        """Sprawdzenie czy plik istnieje w cache"""
        file_path = self.get_file_path(content_id, filename)
        return file_path.exists()

    def save_file(self, content_id: int, filename: str, data: bytes) -> Path:
        """Zapisanie pliku do cache"""
        file_path = self.get_file_path(content_id, filename)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(data)
        return file_path

    def get_file(self, content_id: int, filename: str) -> Optional[Path]:
        """Pobranie pliku z cache"""
        file_path = self.get_file_path(content_id, filename)
        if file_path.exists():
            return file_path
        return None

    def clear_cache(self):
        """Wyczyszczenie cache"""
        for file in self.cache_dir.glob("*"):
            if file.is_file():
                file.unlink()

    def get_cache_size_mb(self) -> float:
        """Pobranie rozmiaru cache w MB"""
        total_size = 0
        for file in self.cache_dir.rglob("*"):
            if file.is_file():
                total_size += file.stat().st_size
        return round(total_size / (1024 * 1024), 2)



