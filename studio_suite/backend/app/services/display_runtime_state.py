"""
In-memory runtime state for display clients.

Used to make bell/music decisions based on the currently played content type
without introducing DB migrations.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from threading import Lock
from typing import Any, Optional

_state_lock = Lock()
_display_state: dict[int, dict[str, Any]] = {}
_STATE_TTL = timedelta(minutes=5)


def update_display_runtime_state(
    display_id: int,
    current_content_id: Optional[int] = None,
    current_content_type: Optional[str] = None,
    is_playing_video: Optional[bool] = None,
) -> None:
    with _state_lock:
        _display_state[display_id] = {
            "current_content_id": current_content_id,
            "current_content_type": (current_content_type or "").lower() or None,
            "is_playing_video": bool(is_playing_video),
            "updated_at": datetime.utcnow(),
        }


def get_display_runtime_state(display_id: int) -> Optional[dict[str, Any]]:
    with _state_lock:
        row = _display_state.get(display_id)
        if not row:
            return None
        if datetime.utcnow() - row["updated_at"] > _STATE_TTL:
            _display_state.pop(display_id, None)
            return None
        return row.copy()


def is_display_playing_video(display_id: int) -> bool:
    row = get_display_runtime_state(display_id)
    if not row:
        return False
    return bool(row.get("is_playing_video")) or row.get("current_content_type") == "video"
