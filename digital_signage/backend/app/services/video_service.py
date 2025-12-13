"""
Serwis do przetwarzania video
"""
import os
import subprocess
from pathlib import Path
from typing import Optional, Tuple

from app.config import settings


def transcode_video(
    input_path: str,
    output_path: str,
    width: int = 1920,
    height: int = 1080,
    fps: int = 30,
    crf: int = 23
) -> Tuple[bool, Optional[str]]:
    """
    Transkodowanie video do MP4 (H.264)
    
    Args:
        input_path: Ścieżka do pliku wejściowego
        output_path: Ścieżka do pliku wyjściowego
        width: Szerokość (domyślnie 1920)
        height: Wysokość (domyślnie 1080)
        fps: Frame rate (domyślnie 30)
        crf: Constant Rate Factor (domyślnie 23, niższe = lepsza jakość)
    
    Returns:
        (success, error_message)
    """
    # Upewnienie się, że katalog wyjściowy istnieje
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Komenda FFmpeg
    cmd = [
        "ffmpeg",
        "-i", input_path,
        "-c:v", "libx264",  # Codec video: H.264
        "-preset", "medium",  # Preset kodowania (medium = balans jakości/czasu)
        "-crf", str(crf),  # Constant Rate Factor
        "-s", f"{width}x{height}",  # Rozdzielczość
        "-r", str(fps),  # Frame rate
        "-c:a", "aac",  # Codec audio: AAC
        "-b:a", "128k",  # Bitrate audio
        "-movflags", "+faststart",  # Optymalizacja dla streaming
        "-y",  # Nadpisz plik wyjściowy jeśli istnieje
        output_path
    ]
    
    try:
        # Uruchomienie FFmpeg
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        return True, None
    except subprocess.CalledProcessError as e:
        error_msg = f"FFmpeg error: {e.stderr}" if e.stderr else str(e)
        return False, error_msg
    except FileNotFoundError:
        return False, "FFmpeg not found. Please install FFmpeg."
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"


def get_video_duration(video_path: str) -> Optional[int]:
    """
    Pobranie długości video w sekundach
    Używa ffprobe
    """
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        video_path
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        duration = float(result.stdout.strip())
        return int(duration)
    except (subprocess.CalledProcessError, ValueError, FileNotFoundError):
        return None


def get_video_info(video_path: str) -> dict:
    """
    Pobranie informacji o video (rozdzielczość, codec, etc.)
    """
    cmd = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,codec_name,r_frame_rate",
        "-of", "json",
        video_path
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        import json
        info = json.loads(result.stdout)
        return info.get("streams", [{}])[0] if info.get("streams") else {}
    except (subprocess.CalledProcessError, ValueError, FileNotFoundError, KeyError):
        return {}

