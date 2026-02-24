#!/usr/bin/env python3
"""
Główny plik klienta wyświetlacza Windows.
"""
import sys
import time
from datetime import datetime, time as dt_time
from pathlib import Path

from cache import CacheManager
import config
from display_client import DisplayClient
from player import ContentPlayer


def _ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _log(message: str) -> None:
    line = f"[{_ts()}] {message}"
    print(line)
    try:
        with open(config.DEBUG_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


class DigitalSignageClient:
    """Główna pętla klienta."""

    def __init__(self):
        self.client = DisplayClient()
        self.cache = CacheManager()
        self.player = ContentPlayer()
        self.current_schedule = []
        self.current_content_id: int | None = None
        self.current_is_test_content: bool = False

    def run(self) -> None:
        _log(f"Start klienta Windows. server={self.client.server_url}, poll={config.POLL_INTERVAL_SECONDS}s")
        self.player.init_display()
        self.player.set_connection_state("connecting")

        next_poll = 0.0

        try:
            while True:
                self.player.pump_events()

                if not self.client.display_id:
                    if not self.client.register():
                        self.player.set_connection_state("error")
                        self.player.display_message("Brak połączenia z serwerem\nPonawianie...")
                        _log("Błąd rejestracji - ponawianie za 5s")
                        for _ in range(50):
                            self.player.pump_events()
                            time.sleep(0.1)
                        continue
                    self.client.start_heartbeat()
                    self.player.set_connection_state("connected")
                    self.player.display_message("Połączono z serwerem\nOczekiwanie na treść...")
                    _log(f"Rejestracja OK. display_id={self.client.display_id}")

                now = time.monotonic()
                if now >= next_poll:
                    next_poll = now + float(config.POLL_INTERVAL_SECONDS)
                    try:
                        self.update_schedule()
                        self.update_content()
                    except Exception as e:
                        _log(f"Błąd pętli głównej: {e}")
                        self.player.set_connection_state("error")

                time.sleep(0.1)
        except KeyboardInterrupt:
            _log("Zatrzymywanie klienta")
            self.client.stop_heartbeat()
            sys.exit(0)

    def update_schedule(self) -> None:
        try:
            schedule = self.client.get_schedule()
            self.current_schedule = schedule or []
            _log(f"Odświeżenie harmonogramu: {len(self.current_schedule)} pozycji")
            self.player.set_connection_state("connected")
        except Exception as e:
            _log(f"Błąd aktualizacji harmonogramu: {e}")
            self.current_schedule = []
            self.player.set_connection_state("error")

    def update_content(self) -> None:
        test_content = self.client.get_test_content()
        if test_content:
            content_id = int(test_content["id"])
            if content_id != self.current_content_id or not self.current_is_test_content:
                _log(f"Aktywna treść testowa: id={content_id}, typ={test_content.get('type')}")
                if self.display_content_from_payload(test_content):
                    self.current_content_id = content_id
                    self.current_is_test_content = True
                    _log("Treść testowa odtworzona")
                else:
                    self.current_content_id = None
                    self.current_is_test_content = False
                    _log("Treść testowa nieudana - ponowię przy następnym cyklu")
            return

        if self.current_is_test_content:
            _log("Treść testowa usunięta - powrót do harmonogramu")
            self.current_content_id = None
            self.current_is_test_content = False

        if not self.current_schedule:
            if self.current_content_id is not None:
                self.current_content_id = None
                self.client.set_runtime_content_state(None, None, False)
            self.player.display_message("Połączono z serwerem\nBrak aktywnej treści")
            return

        now = datetime.now().time()
        current_schedule_item = None

        for item in self.current_schedule:
            start_time = self._parse_schedule_time(item["start_time"])
            end_time = self._parse_schedule_time(item["end_time"])
            if not start_time or not end_time:
                continue
            if start_time <= now <= end_time:
                current_schedule_item = item
                break

        if current_schedule_item:
            content_id = int(current_schedule_item["content_id"])
            if content_id != self.current_content_id:
                _log(f"Aktywna treść z harmonogramu: id={content_id}")
                if self.display_content(content_id):
                    self.current_content_id = content_id
                    _log("Treść z harmonogramu odtworzona")
                else:
                    self.current_content_id = None
                    _log("Treść z harmonogramu nieudana - ponowię przy następnym cyklu")
        else:
            if self.current_content_id is not None:
                self.current_content_id = None
                self.client.set_runtime_content_state(None, None, False)
            self.player.display_message("Połączono z serwerem\nBrak treści o tej godzinie")

    def display_content(self, content_id: int) -> bool:
        _log(f"Pobieranie metadanych treści: id={content_id}")

        try:
            response = self.client.session.get(f"{self.client.server_url}/content/{content_id}", timeout=10)
            if response.status_code != 200:
                _log(f"Błąd metadanych treści: status={response.status_code}")
                self.player.display_message("Błąd pobierania treści")
                return False

            content = response.json()
            return self.display_content_from_payload(content)
        except Exception as e:
            _log(f"Wyjątek podczas pobierania treści {content_id}: {e}")
            self.player.display_message("Wyjątek podczas pobierania treści")
            return False

    def display_content_from_payload(self, content: dict) -> bool:
        content_id = int(content["id"])
        file_path_value = content.get("file_path") or content.get("path") or ""
        filename = Path(file_path_value).name if file_path_value else f"content_{content_id}"

        cached_file = self.cache.get_file(content_id, filename)
        if cached_file:
            _log(f"Cache HIT: {cached_file}")
            return self._play_content(content, cached_file)

        _log(f"Cache MISS -> pobieram plik treści id={content_id}, filename={filename}")
        cache_path = self.cache.get_file_path(content_id, filename)
        if self.client.download_content(content_id, str(cache_path)):
            _log(f"Pobrano plik do cache: {cache_path}")
            return self._play_content(content, cache_path)

        self.player.display_message("Błąd pobierania pliku treści")
        return False

    def _play_content(self, content: dict, file_path: Path) -> bool:
        content_type = content.get("type", "")
        self.client.set_runtime_content_state(
            self.current_content_id,
            content_type,
            content_type == "video",
        )

        _log(f"Odtwarzanie: type={content_type}, path={file_path}")
        if content_type == "image":
            return self.player.display_image(file_path)
        if content_type == "pdf":
            return self.player.display_pdf(file_path)
        if content_type == "excel":
            return self.player.display_excel(file_path)
        if content_type == "video":
            return self.player.display_video(file_path)

        _log(f"Nieobsługiwany typ treści: {content_type}")
        self.player.display_message(f"Nieobsługiwany typ treści: {content_type}")
        return False

    @staticmethod
    def _parse_schedule_time(value: str) -> dt_time | None:
        for fmt in ("%H:%M:%S", "%H:%M"):
            try:
                return datetime.strptime(value, fmt).time()
            except ValueError:
                continue
        _log(f"Nieprawidłowy format czasu w harmonogramie: {value}")
        return None


if __name__ == "__main__":
    client = DigitalSignageClient()
    client.run()
