#!/usr/bin/env python3
"""
Simple Windows bell client.

Features:
- registers as display
- sends heartbeat
- polls bell play command
- downloads bell sound file
- plays audio locally (WAV/MP3) using Windows MCI
- reports playback status to backend
"""
from __future__ import annotations

import ctypes
import os
import socket
import tempfile
import time
import uuid
from pathlib import Path
from typing import Optional

import requests


SERVER_URL = os.getenv("SERVER_URL", "https://dev2.witold.ovh/api/v1").rstrip("/")
MAC_ADDRESS = os.getenv(
    "MAC_ADDRESS",
    ":".join([f"{(uuid.getnode() >> bits) & 0xFF:02x}" for bits in range(0, 2 * 6, 2)][::-1]),
)
POLL_INTERVAL = float(os.getenv("POLL_INTERVAL", "2"))
HEARTBEAT_INTERVAL = float(os.getenv("HEARTBEAT_INTERVAL", "30"))
CACHE_DIR = Path(os.getenv("CACHE_DIR", str(Path(tempfile.gettempdir()) / "ds_windows_bell_cache")))
RESOLUTION_WIDTH = int(os.getenv("RESOLUTION_WIDTH", "1"))
RESOLUTION_HEIGHT = int(os.getenv("RESOLUTION_HEIGHT", "1"))
VERIFY_TLS = os.getenv("VERIFY_TLS", "true").lower() not in {"0", "false", "no"}


def _local_ip() -> str:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("8.8.8.8", 80))
        ip = sock.getsockname()[0]
        sock.close()
        return ip
    except Exception:
        return "127.0.0.1"


def _mci_send(command: str) -> None:
    err = ctypes.windll.winmm.mciSendStringW(command, None, 0, 0)
    if err != 0:
        raise RuntimeError(f"MCI error {err} for command: {command}")


def play_audio(file_path: Path, volume_percent: int) -> None:
    alias = f"bell_{int(time.time() * 1000)}"
    safe_path = str(file_path).replace('"', '\\"')
    volume = max(0, min(1000, int(volume_percent * 10)))

    _mci_send(f'open "{safe_path}" alias {alias}')
    try:
        _mci_send(f"setaudio {alias} volume to {volume}")
        _mci_send(f"play {alias} wait")
    finally:
        try:
            _mci_send(f"close {alias}")
        except Exception:
            pass


class WindowsBellClient:
    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.verify = VERIFY_TLS
        self.display_id: Optional[int] = None
        self.last_heartbeat = 0.0
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def register(self) -> None:
        payload = {
            "mac_address": MAC_ADDRESS,
            "ip_address": _local_ip(),
            "resolution_width": RESOLUTION_WIDTH,
            "resolution_height": RESOLUTION_HEIGHT,
        }
        response = self.session.post(f"{SERVER_URL}/displays/register", json=payload, timeout=15)
        response.raise_for_status()
        self.display_id = response.json()["id"]
        print(f"[ok] registered display_id={self.display_id}, mac={MAC_ADDRESS}")

    def send_heartbeat(self) -> None:
        assert self.display_id is not None
        payload = {
            "current_content_id": None,
            "cache_status": {"windows_bell_client": True},
            "errors": [],
        }
        response = self.session.post(
            f"{SERVER_URL}/displays/{self.display_id}/heartbeat",
            json=payload,
            timeout=15,
        )
        response.raise_for_status()

    def get_bell_command(self) -> Optional[dict]:
        assert self.display_id is not None
        response = self.session.get(
            f"{SERVER_URL}/bells/display/{self.display_id}/play-command",
            timeout=15,
        )
        response.raise_for_status()
        if not response.text or response.text == "null":
            return None
        return response.json()

    def download_bell_sound(self, bell_id: int) -> Path:
        response = self.session.get(
            f"{SERVER_URL}/bells/{bell_id}/sound-file",
            stream=True,
            timeout=30,
        )
        response.raise_for_status()

        filename = f"bell_{bell_id}.bin"
        content_disposition = response.headers.get("Content-Disposition", "")
        if "filename=" in content_disposition:
            filename = content_disposition.split("filename=")[-1].strip().strip('"')

        target = CACHE_DIR / filename
        with open(target, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        return target

    def mark_played(self, bell_id: int, status: str, error_message: Optional[str]) -> None:
        payload = {
            "bell_schedule_id": bell_id,
            "display_id": self.display_id,
            "status": status,
            "error_message": error_message,
        }
        response = self.session.post(f"{SERVER_URL}/bells/mark-played", json=payload, timeout=15)
        response.raise_for_status()

    def run(self) -> None:
        print(f"Windows bell client starting. server={SERVER_URL}")
        while True:
            try:
                if not self.display_id:
                    self.register()

                now = time.time()
                if now - self.last_heartbeat >= HEARTBEAT_INTERVAL:
                    self.send_heartbeat()
                    self.last_heartbeat = now

                cmd = self.get_bell_command()
                if not cmd or not cmd.get("bell_schedule_id"):
                    time.sleep(POLL_INTERVAL)
                    continue

                bell_id = int(cmd["bell_schedule_id"])
                volume = int(cmd.get("volume", 50))
                status = "played"
                err_msg = None

                try:
                    audio_path = self.download_bell_sound(bell_id)
                    play_audio(audio_path, volume)
                    print(f"[ok] played bell_id={bell_id} file={audio_path.name}")
                except Exception as exc:
                    status = "failed"
                    err_msg = str(exc)
                    print(f"[error] bell_id={bell_id} failed: {exc}")

                self.mark_played(bell_id, status, err_msg)
                time.sleep(POLL_INTERVAL)
            except KeyboardInterrupt:
                print("Stopping...")
                return
            except Exception as exc:
                print(f"[error] loop: {exc}")
                time.sleep(3)


if __name__ == "__main__":
    WindowsBellClient().run()
