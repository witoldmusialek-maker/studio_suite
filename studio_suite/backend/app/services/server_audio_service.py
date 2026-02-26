"""
Server-side audio playback service for school bells.

Playback is intentionally command-driven via environment variable
`BELL_SERVER_PLAYER_CMD` to avoid hard dependency on specific audio libraries.
"""
from __future__ import annotations

import os
import subprocess
from typing import Tuple

from app.config import settings


def play_bell_on_server(file_path: str, volume_percent: int) -> Tuple[bool, str]:
    """
    Attempt local playback on server machine.

    Command template is provided by `BELL_SERVER_PLAYER_CMD` and supports:
    - {file_path}
    - {volume_percent}
    - {volume_float} (0.0-1.0)
    """
    if not settings.BELL_SERVER_PLAYBACK_ENABLED:
        return False, "Server playback is disabled"

    if not file_path:
        return False, "No sound file path"

    resolved_path = _resolve_audio_path(file_path)
    if not os.path.exists(resolved_path):
        return False, f"Audio file not found: {resolved_path}"

    cmd_template = (settings.BELL_SERVER_PLAYER_CMD or "").strip()
    if not cmd_template:
        return False, "BELL_SERVER_PLAYER_CMD is not configured"

    volume = max(0, min(100, int(volume_percent)))
    volume_float = volume / 100.0
    command = cmd_template.format(
        file_path=resolved_path,
        volume_percent=volume,
        volume_float=volume_float,
    )

    try:
        subprocess.run(
            command,
            shell=True,
            check=True,
            timeout=settings.BELL_SERVER_PLAYER_TIMEOUT_SEC,
        )
        return True, f"Played on server: {resolved_path}"
    except subprocess.TimeoutExpired:
        return False, f"Playback timeout after {settings.BELL_SERVER_PLAYER_TIMEOUT_SEC}s"
    except subprocess.CalledProcessError as exc:
        return False, f"Playback command failed (exit {exc.returncode})"
    except Exception as exc:  # pragma: no cover
        return False, f"Playback error: {exc}"


def _resolve_audio_path(file_path: str) -> str:
    normalized = os.path.normpath(file_path)
    if os.path.isabs(normalized):
        return normalized

    # Prefer path relative to current working directory if it already exists.
    if os.path.exists(normalized):
        return normalized

    return os.path.normpath(os.path.join(settings.CONTENT_DIR, normalized))
