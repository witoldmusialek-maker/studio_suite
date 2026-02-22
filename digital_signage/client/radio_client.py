"""
Radio Bell Client
-----------------
Runs on server node (e.g. T620) and acts as an audio-only "display" client:
- registers as display
- polls bell play command
- downloads bell audio file
- plays it locally
- confirms playback to backend
"""
from __future__ import annotations

import os
import socket
import sys
import time
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import requests

try:
    import vlc  # type: ignore
except Exception:
    vlc = None

try:
    import radio_config as cfg
except Exception:
    # Fallback to environment variables.
    class cfg:  # type: ignore
        SERVER_URL = os.getenv("SERVER_URL", "http://localhost:8000/api/v1")
        MAC_ADDRESS = os.getenv("MAC_ADDRESS", "02:AA:BB:CC:DD:EE")
        DISPLAY_NAME = os.getenv("DISPLAY_NAME", "radio-node-t620")
        RESOLUTION_WIDTH = int(os.getenv("RESOLUTION_WIDTH", "1"))
        RESOLUTION_HEIGHT = int(os.getenv("RESOLUTION_HEIGHT", "1"))
        POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "2"))
        HEARTBEAT_INTERVAL = int(os.getenv("HEARTBEAT_INTERVAL", "30"))
        CACHE_DIR = os.getenv("CACHE_DIR", "./radio_cache")


class RadioBellClient:
    def __init__(self) -> None:
        self.session = requests.Session()
        self.display_id: Optional[int] = None
        self.last_heartbeat = 0.0
        self.cache_dir = Path(cfg.CACHE_DIR)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.current_music_schedule_id: Optional[int] = None
        self.music_track_index = 0

    def run(self) -> None:
        print("Radio Bell Client starting...")
        while True:
            try:
                if not self.display_id:
                    self.register()
                self.tick()
            except KeyboardInterrupt:
                print("Stopping by keyboard interrupt")
                return
            except Exception as exc:
                print(f"[error] main loop: {exc}")
                time.sleep(3)

    def register(self) -> None:
        payload = {
            "mac_address": cfg.MAC_ADDRESS,
            "ip_address": self._local_ip(),
            "resolution_width": cfg.RESOLUTION_WIDTH,
            "resolution_height": cfg.RESOLUTION_HEIGHT,
        }
        response = self.session.post(f"{cfg.SERVER_URL}/displays/register", json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        self.display_id = data["id"]
        print(f"Registered display_id={self.display_id} name={cfg.DISPLAY_NAME}")

    def tick(self) -> None:
        if not self.display_id:
            return

        now = time.time()
        if now - self.last_heartbeat >= cfg.HEARTBEAT_INTERVAL:
            self.send_heartbeat()
            self.last_heartbeat = now

        cmd = self.get_bell_command()
        if cmd and cmd.get("bell_schedule_id"):
            bell_id = cmd["bell_schedule_id"]
            status = "played"
            error_message = None
            try:
                audio_file = self.download_bell_file(bell_id)
                self.play_audio(audio_file, int(cmd.get("volume", 50)))
                print(f"Bell played: bell_id={bell_id}, file={audio_file}")
            except Exception as exc:
                status = "failed"
                error_message = str(exc)
                print(f"[error] playback failed for bell_id={bell_id}: {exc}")

            self.mark_played(bell_id, status, error_message)
            time.sleep(cfg.POLL_INTERVAL)
            return

        # No bell right now: optionally play break music playlist.
        self.tick_music_playlist()
        time.sleep(cfg.POLL_INTERVAL)

    def get_bell_command(self) -> Optional[dict]:
        assert self.display_id is not None
        response = self.session.get(
            f"{cfg.SERVER_URL}/bells/display/{self.display_id}/play-command",
            timeout=10,
        )
        response.raise_for_status()
        if not response.text or response.text == "null":
            return None
        return response.json()

    def download_bell_file(self, bell_id: int) -> Path:
        response = self.session.get(
            f"{cfg.SERVER_URL}/bells/{bell_id}/sound-file",
            timeout=30,
            stream=True,
        )
        response.raise_for_status()

        filename = f"bell_{bell_id}.bin"
        content_disposition = response.headers.get("Content-Disposition", "")
        if "filename=" in content_disposition:
            filename = content_disposition.split("filename=")[-1].strip().strip('"')
        target = self.cache_dir / filename

        with open(target, "wb") as out:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    out.write(chunk)

        return target

    def tick_music_playlist(self) -> None:
        playlist = self.get_music_playlist()
        if not playlist or not playlist.get("active"):
            self.current_music_schedule_id = None
            self.music_track_index = 0
            return

        schedule = playlist.get("schedule") or {}
        tracks = playlist.get("tracks") or []
        if not tracks:
            return

        schedule_id = schedule.get("id")
        if schedule_id != self.current_music_schedule_id:
            self.current_music_schedule_id = schedule_id
            self.music_track_index = 0

        track = tracks[self.music_track_index % len(tracks)]
        self.music_track_index += 1

        volume = int(schedule.get("volume", 50))
        title = track.get("title") or f"track#{track.get('id')}"
        try:
            audio_file = self.download_track_file(track)
            self.play_audio(audio_file, volume)
            print(f"Break music played: {title} ({audio_file.name})")
        except Exception as exc:
            print(f"[error] break music playback failed for {title}: {exc}")

    def get_music_playlist(self) -> Optional[dict]:
        assert self.display_id is not None
        response = self.session.get(
            f"{cfg.SERVER_URL}/bells/display/{self.display_id}/music-playlist",
            timeout=10,
        )
        response.raise_for_status()
        return response.json()

    def download_track_file(self, track: dict) -> Path:
        track_id = track.get("id")
        file_url = track.get("file_url")
        if not file_url:
            raise RuntimeError("Track file_url is missing")

        resolved_url = self._absolute_api_url(str(file_url))
        response = self.session.get(resolved_url, timeout=30, stream=True)
        response.raise_for_status()

        filename = f"track_{track_id}.bin"
        content_disposition = response.headers.get("Content-Disposition", "")
        if "filename=" in content_disposition:
            filename = content_disposition.split("filename=")[-1].strip().strip('"')
        target = self.cache_dir / filename

        with open(target, "wb") as out:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    out.write(chunk)

        return target

    def play_audio(self, file_path: Path, volume_percent: int) -> None:
        ext = file_path.suffix.lower()

        if vlc is not None:
            player = vlc.MediaPlayer(str(file_path))
            player.audio_set_volume(max(0, min(100, volume_percent)))
            player.play()
            # Wait until playback completes.
            for _ in range(600):
                state = player.get_state()
                if state in (vlc.State.Ended, vlc.State.Stopped):
                    break
                if state == vlc.State.Error:
                    raise RuntimeError("VLC playback error")
                time.sleep(0.2)
            player.stop()
            return

        if sys.platform == "win32" and ext == ".wav":
            import winsound

            winsound.PlaySound(str(file_path), winsound.SND_FILENAME)
            return

        raise RuntimeError("No audio backend available (install python-vlc, or use WAV on Windows)")

    def mark_played(self, bell_id: int, status: str, error_message: Optional[str]) -> None:
        payload = {
            "bell_schedule_id": bell_id,
            "display_id": self.display_id,
            "status": status,
            "error_message": error_message,
        }
        response = self.session.post(f"{cfg.SERVER_URL}/bells/mark-played", json=payload, timeout=10)
        response.raise_for_status()

    def send_heartbeat(self) -> None:
        assert self.display_id is not None
        payload = {
            "current_content_id": None,
            "cache_status": {"radio_client": True},
            "errors": [],
        }
        response = self.session.post(
            f"{cfg.SERVER_URL}/displays/{self.display_id}/heartbeat",
            json=payload,
            timeout=10,
        )
        response.raise_for_status()

    @staticmethod
    def _absolute_api_url(path_or_url: str) -> str:
        if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
            return path_or_url
        if path_or_url.startswith("/"):
            parsed = urlparse(cfg.SERVER_URL)
            return f"{parsed.scheme}://{parsed.netloc}{path_or_url}"
        return f"{cfg.SERVER_URL.rstrip('/')}/{path_or_url.lstrip('/')}"

    @staticmethod
    def _local_ip() -> str:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"


if __name__ == "__main__":
    RadioBellClient().run()
