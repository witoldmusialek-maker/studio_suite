#!/usr/bin/env python3
"""
Glowny plik aplikacji klienta wyswietlacza
"""
import sys
import time
from datetime import datetime, time as dt_time
from pathlib import Path

from cache import CacheManager
import config
from display_client import DisplayClient
from player import ContentPlayer


class DigitalSignageClient:
    """Glowna klasa klienta."""

    def __init__(self):
        self.client = DisplayClient()
        self.cache = CacheManager()
        self.player = ContentPlayer()
        self.current_schedule = []
        self.current_content_id: int | None = None

    def run(self):
        """Uruchomienie klienta."""
        print("Uruchamianie klienta Digital Signage...")

        # Inicjalizacja wyswietlacza
        self.player.init_display()

        # Glowna petla
        try:
            while True:
                if not self.client.display_id:
                    if not self.client.register():
                        print("Blad rejestracji - ponawianie za 5s...")
                        time.sleep(5)
                        continue
                    self.client.start_heartbeat()

                try:
                    self.update_schedule()
                    self.update_content()
                except Exception as e:
                    # Nie zamykaj procesu przez pojedynczy blad runtime
                    print(f"Blad petli glownej: {e}")

                time.sleep(10)
        except KeyboardInterrupt:
            print("\nZatrzymywanie klienta...")
            self.client.stop_heartbeat()
            sys.exit(0)

    def update_schedule(self):
        """Aktualizacja harmonogramu."""
        try:
            schedule = self.client.get_schedule()
            if schedule:
                self.current_schedule = schedule
                print(f"Zaktualizowano harmonogram: {len(schedule)} pozycji")
        except Exception as e:
            print(f"Blad aktualizacji harmonogramu: {e}")

    def update_content(self):
        """Aktualizacja wyswietlanej tresci."""
        if not self.current_schedule:
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
            content_id = current_schedule_item["content_id"]
            if content_id != self.current_content_id:
                self.display_content(content_id)
                self.current_content_id = content_id
        else:
            if self.current_content_id is not None:
                self.current_content_id = None
                self.client.set_runtime_content_state(None, None, False)
                print("Brak harmonogramu - oczekiwanie...")

    def display_content(self, content_id: int):
        """Wyswietlenie tresci."""
        print(f"Wyswietlanie tresci ID: {content_id}")

        try:
            response = self.client.session.get(f"{self.client.server_url}/content/{content_id}")
            if response.status_code != 200:
                print(f"Blad pobierania tresci: {response.status_code}")
                return

            content = response.json()
            filename = Path(content["file_path"]).name

            cached_file = self.cache.get_file(content_id, filename)
            if cached_file:
                print(f"Uzywanie cache: {cached_file}")
                self._play_content(content, cached_file)
            else:
                print("Pobieranie tresci z serwera...")
                cache_path = self.cache.get_file_path(content_id, filename)
                if self.client.download_content(content_id, str(cache_path)):
                    print(f"Zapisano do cache: {cache_path}")
                    self._play_content(content, cache_path)
        except Exception as e:
            print(f"Blad wyswietlania tresci: {e}")

    def _play_content(self, content: dict, file_path: Path):
        """Odtworzenie tresci."""
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

    @staticmethod
    def _parse_schedule_time(value: str) -> dt_time | None:
        """Akceptuje format HH:MM:SS oraz HH:MM."""
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
