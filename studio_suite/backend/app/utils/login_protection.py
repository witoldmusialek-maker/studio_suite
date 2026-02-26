"""
Simple in-memory protection against brute-force login attempts.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Dict, List


@dataclass
class AttemptState:
    failed_attempts: List[datetime] = field(default_factory=list)
    locked_until: datetime | None = None


class LoginProtection:
    def __init__(self, max_attempts: int, window_seconds: int, lockout_seconds: int) -> None:
        self.max_attempts = max_attempts
        self.window = timedelta(seconds=window_seconds)
        self.lockout = timedelta(seconds=lockout_seconds)
        self._states: Dict[str, AttemptState] = {}
        self._lock = Lock()

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _prune(self, state: AttemptState, now: datetime) -> None:
        state.failed_attempts = [t for t in state.failed_attempts if now - t <= self.window]
        if state.locked_until and state.locked_until <= now:
            state.locked_until = None

    def is_blocked(self, key: str) -> int:
        now = self._now()
        with self._lock:
            state = self._states.get(key)
            if not state:
                return 0
            self._prune(state, now)
            if state.locked_until:
                return max(0, int((state.locked_until - now).total_seconds()))
            return 0

    def register_failure(self, key: str) -> int:
        now = self._now()
        with self._lock:
            state = self._states.setdefault(key, AttemptState())
            self._prune(state, now)
            state.failed_attempts.append(now)
            if len(state.failed_attempts) >= self.max_attempts:
                state.locked_until = now + self.lockout
                state.failed_attempts.clear()
                return int(self.lockout.total_seconds())
            return 0

    def reset(self, key: str) -> None:
        with self._lock:
            self._states.pop(key, None)

