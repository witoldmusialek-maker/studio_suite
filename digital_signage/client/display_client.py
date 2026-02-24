"""
Display client HTTP communication.
"""
import threading
import time
from typing import Any, Dict, Optional

import requests

import config


class DisplayClient:
    """Client for communication with backend API."""

    def __init__(self):
        self.server_url = config.SERVER_URL.rstrip("/")
        self.mac_address = config.MAC_ADDRESS
        self.display_id: Optional[int] = None
        self.session = requests.Session()
        self.running = False
        self.heartbeat_thread: Optional[threading.Thread] = None
        self.current_content_id: Optional[int] = None
        self.current_content_type: Optional[str] = None
        self.is_playing_video: bool = False

    def register(self) -> bool:
        try:
            response = self.session.post(
                f"{self.server_url}/displays/register",
                json={
                    "mac_address": self.mac_address,
                    "ip_address": self._get_local_ip(),
                    "resolution_width": config.RESOLUTION_WIDTH,
                    "resolution_height": config.RESOLUTION_HEIGHT,
                },
                timeout=10,
            )
            if response.status_code == 201:
                data = response.json()
                self.display_id = data["id"]
                print(f"[ok] registered display_id={self.display_id}, mac={self.mac_address}")
                return True

            print(f"[error] register: {response.status_code} {response.text[:200]}")
            return False
        except Exception as e:
            print(f"[error] register: {e}")
            return False

    def get_schedule(self) -> list:
        if not self.display_id:
            return []

        try:
            response = self.session.get(
                f"{self.server_url}/schedules/display/{self.display_id}/schedule",
                timeout=10,
            )
            if response.status_code == 200:
                return response.json()
            print(f"[warn] schedule: {response.status_code}")
        except Exception as e:
            print(f"[error] schedule: {e}")
        return []

    def get_test_content(self) -> Optional[Dict[str, Any]]:
        """Returns test content payload with 'content' key, or None."""
        if not self.display_id:
            return None

        try:
            response = self.session.get(
                f"{self.server_url}/displays/{self.display_id}/test-content",
                timeout=10,
            )
            if response.status_code != 200:
                return None

            payload = response.json()
            content = payload.get("content") if isinstance(payload, dict) else None
            return content if isinstance(content, dict) else None
        except Exception as e:
            print(f"[error] test-content: {e}")
            return None

    def set_runtime_content_state(
        self,
        current_content_id: Optional[int],
        current_content_type: Optional[str],
        is_playing_video: bool,
    ) -> None:
        self.current_content_id = current_content_id
        self.current_content_type = current_content_type
        self.is_playing_video = is_playing_video

    def send_heartbeat(self, current_content_id: Optional[int] = None) -> bool:
        if not self.display_id:
            return False

        try:
            payload_content_id = (
                current_content_id if current_content_id is not None else self.current_content_id
            )
            response = self.session.post(
                f"{self.server_url}/displays/{self.display_id}/heartbeat",
                json={
                    "current_content_id": payload_content_id,
                    "current_content_type": self.current_content_type,
                    "is_playing_video": self.is_playing_video,
                    "cache_status": {},
                    "errors": [],
                },
                timeout=10,
            )
            return response.status_code == 200
        except Exception as e:
            print(f"[error] heartbeat: {e}")
            return False

    def download_content(self, content_id: int, file_path: str) -> bool:
        try:
            response = self.session.get(
                f"{self.server_url}/content/{content_id}/download",
                stream=True,
                timeout=30,
            )
            if response.status_code == 200:
                with open(file_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                return True

            print(f"[error] download {content_id}: {response.status_code}")
        except Exception as e:
            print(f"[error] download {content_id}: {e}")
        return False

    def start_heartbeat(self) -> None:
        if self.running:
            return
        self.running = True
        self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self.heartbeat_thread.start()

    def stop_heartbeat(self) -> None:
        self.running = False
        if self.heartbeat_thread:
            self.heartbeat_thread.join(timeout=2)

    def _heartbeat_loop(self) -> None:
        while self.running:
            self.send_heartbeat()
            time.sleep(config.HEARTBEAT_INTERVAL)

    def _get_local_ip(self) -> str:
        try:
            import socket

            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"
