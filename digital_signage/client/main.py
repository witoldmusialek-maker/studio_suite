#!/usr/bin/env python3
"""
Main file for Windows display client.
"""
import sys
import time
from datetime import datetime, time as dt_time
from pathlib import Path

from cache import CacheManager
from display_client import DisplayClient
from player import ContentPlayer


class DigitalSignageClient:
    """Main client loop."""

    def __init__(self):
        self.client = DisplayClient()
        self.cache = CacheManager()
        self.player = ContentPlayer()
        self.current_schedule = []
        self.current_content_id: int | None = None
        self.current_is_test_content: bool = False

    def run(self) -> None:
        print(f"Windows display client starting. server={self.client.server_url}")
        self.player.init_display()
        self.player.set_connection_state("connecting")

        next_poll = 0.0

        try:
            while True:
                self.player.pump_events()

                if not self.client.display_id:
                    if not self.client.register():
                        self.player.set_connection_state("error")
                        self.player.display_message("Brak polaczenia z serwerem\nPonawianie...")
                        print("Blad rejestracji - ponawianie za 5s...")
                        for _ in range(50):
                            self.player.pump_events()
                            time.sleep(0.1)
                        continue
                    self.client.start_heartbeat()
                    self.player.set_connection_state("connected")
                    self.player.display_message("Polaczono z serwerem\nOczekiwanie na tresc...")

                now = time.monotonic()
                if now >= next_poll:
                    next_poll = now + 10.0
                    try:
                        self.update_schedule()
                        self.update_content()
                    except Exception as e:
                        print(f"Blad petli glownej: {e}")
                        self.player.set_connection_state("error")

                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nZatrzymywanie klienta...")
            self.client.stop_heartbeat()
            sys.exit(0)

    def update_schedule(self) -> None:
        try:
            schedule = self.client.get_schedule()
            self.current_schedule = schedule or []
            print(f"Harmonogram: {len(self.current_schedule)} pozycji")
            self.player.set_connection_state("connected")
        except Exception as e:
            print(f"Blad aktualizacji harmonogramu: {e}")
            self.current_schedule = []
            self.player.set_connection_state("error")

    def update_content(self) -> None:
        # Priority 1: test content from backend (same behavior as Android client)
        test_content = self.client.get_test_content()
        if test_content:
            content_id = int(test_content["id"])
            if content_id != self.current_content_id or not self.current_is_test_content:
                print(f"Test content active: {content_id}")
                self.display_content_from_payload(test_content)
                self.current_content_id = content_id
                self.current_is_test_content = True
            return

        # When test content was cleared, force refresh regular content on next match
        if self.current_is_test_content:
            self.current_content_id = None
            self.current_is_test_content = False

        if not self.current_schedule:
            if self.current_content_id is not None:
                self.current_content_id = None
                self.client.set_runtime_content_state(None, None, False)
            self.player.display_message("Polaczono z serwerem\nBrak aktywnej tresci")
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
                self.display_content(content_id)
                self.current_content_id = content_id
        else:
            if self.current_content_id is not None:
                self.current_content_id = None
                self.client.set_runtime_content_state(None, None, False)
            self.player.display_message("Polaczono z serwerem\nBrak tresci o tej godzinie")

    def display_content(self, content_id: int) -> None:
        print(f"Wyswietlanie tresci ID: {content_id}")

        try:
            response = self.client.session.get(f"{self.client.server_url}/content/{content_id}", timeout=10)
            if response.status_code != 200:
                print(f"Blad pobierania tresci: {response.status_code}")
                self.player.display_message("Blad pobierania tresci")
                return

            content = response.json()
            self.display_content_from_payload(content)
        except Exception as e:
            print(f"Blad wyswietlania tresci: {e}")
            self.player.display_message("Wyjatek podczas wyswietlania tresci")

    def display_content_from_payload(self, content: dict) -> None:
        content_id = int(content["id"])
        file_path_value = content.get("file_path") or content.get("path") or ""
        filename = Path(file_path_value).name if file_path_value else f"content_{content_id}"

        cached_file = self.cache.get_file(content_id, filename)
        if cached_file:
            print(f"Uzywanie cache: {cached_file}")
            self._play_content(content, cached_file)
            return

        print("Pobieranie tresci z serwera...")
        cache_path = self.cache.get_file_path(content_id, filename)
        if self.client.download_content(content_id, str(cache_path)):
            print(f"Zapisano do cache: {cache_path}")
            self._play_content(content, cache_path)
        else:
            self.player.display_message("Blad pobierania pliku tresci")

    def _play_content(self, content: dict, file_path: Path) -> None:
        content_type = content["type"]
        self.client.set_runtime_content_state(
            self.current_content_id,
            content_type,
            content_type == "video",
        )

        if content_type == "image":
            self.player.display_image(file_path)
        elif content_type == "pdf":
            self.player.display_pdf(file_path)
        elif content_type == "excel":
            self.player.display_excel(file_path)
        elif content_type == "video":
            self.player.display_video(file_path)
        else:
            print(f"Nieobslugiwany typ tresci: {content_type}")
            self.player.display_message(f"Nieobslugiwany typ tresci: {content_type}")

    @staticmethod
    def _parse_schedule_time(value: str) -> dt_time | None:
        for fmt in ("%H:%M:%S", "%H:%M"):
            try:
                return datetime.strptime(value, fmt).time()
            except ValueError:
                continue
        print(f"Nieprawidlowy format czasu w harmonogramie: {value}")
        return None


if __name__ == "__main__":
    client = DigitalSignageClient()
    client.run()
