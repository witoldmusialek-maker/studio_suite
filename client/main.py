#!/usr/bin/env python3
"""
GĹ‚Ăłwny plik aplikacji klienta wyĹ›wietlacza
"""
import time
import sys
from pathlib import Path
from datetime import datetime, time as dt_time

from display_client import DisplayClient
from cache import CacheManager
from player import ContentPlayer
import config


class DigitalSignageClient:
    """GĹ‚Ăłwna klasa klienta"""

    def __init__(self):
        self.client = DisplayClient()
        self.cache = CacheManager()
        self.player = ContentPlayer()
        self.current_schedule = []
        self.current_content_id: int | None = None

    def run(self):
        """Uruchomienie klienta"""
        print("Uruchamianie klienta Studio Suite...")

        # Inicjalizacja wyĹ›wietlacza
        self.player.init_display()

        # Rejestracja na serwerze
        if not self.client.register():
            print("BĹ‚Ä…d rejestracji - zakoĹ„czenie")
            return

        # Uruchomienie heartbeat
        self.client.start_heartbeat()

        # GĹ‚Ăłwna pÄ™tla
        try:
            while True:
                self.update_schedule()
                self.update_content()
                time.sleep(10)  # Sprawdzanie co 10 sekund
        except KeyboardInterrupt:
            print("\nZatrzymywanie klienta...")
            self.client.stop_heartbeat()
            sys.exit(0)

    def update_schedule(self):
        """Aktualizacja harmonogramu"""
        try:
            schedule = self.client.get_schedule()
            if schedule:
                self.current_schedule = schedule
                print(f"Zaktualizowano harmonogram: {len(schedule)} pozycji")
        except Exception as e:
            print(f"BĹ‚Ä…d aktualizacji harmonogramu: {e}")

    def update_content(self):
        """Aktualizacja wyĹ›wietlanej treĹ›ci"""
        if not self.current_schedule:
            return

        now = datetime.now().time()
        current_schedule_item = None

        # ZnajdĹş aktualny harmonogram
        for item in self.current_schedule:
            start_time = datetime.strptime(item["start_time"], "%H:%M:%S").time()
            end_time = datetime.strptime(item["end_time"], "%H:%M:%S").time()

            if start_time <= now <= end_time:
                current_schedule_item = item
                break

        if current_schedule_item:
            content_id = current_schedule_item["content_id"]
            
            # JeĹ›li treĹ›Ä‡ siÄ™ zmieniĹ‚a
            if content_id != self.current_content_id:
                self.display_content(content_id)
                self.current_content_id = content_id
        else:
            # Brak harmonogramu - wyĹ›wietl domyĹ›lny ekran
            if self.current_content_id is not None:
                self.current_content_id = None
                print("Brak harmonogramu - oczekiwanie...")

    def display_content(self, content_id: int):
        """WyĹ›wietlenie treĹ›ci"""
        print(f"WyĹ›wietlanie treĹ›ci ID: {content_id}")

        # Pobranie informacji o treĹ›ci
        try:
            response = self.client.session.get(
                f"{self.client.server_url}/content/{content_id}"
            )
            if response.status_code != 200:
                print(f"BĹ‚Ä…d pobierania treĹ›ci: {response.status_code}")
                return

            content = response.json()
            filename = Path(content["file_path"]).name

            # Sprawdzenie cache
            cached_file = self.cache.get_file(content_id, filename)
            if cached_file:
                print(f"UĹĽywanie cache: {cached_file}")
                self._play_content(content, cached_file)
            else:
                # Pobranie z serwera
                print(f"Pobieranie treĹ›ci z serwera...")
                cache_path = self.cache.get_file_path(content_id, filename)
                if self.client.download_content(content_id, str(cache_path)):
                    print(f"Zapisano do cache: {cache_path}")
                    self._play_content(content, cache_path)
        except Exception as e:
            print(f"BĹ‚Ä…d wyĹ›wietlania treĹ›ci: {e}")

    def _play_content(self, content: dict, file_path: Path):
        """Odtworzenie treĹ›ci"""
        content_type = content["type"]

        if content_type == "image":
            self.player.display_image(file_path)
        elif content_type == "pdf":
            self.player.display_pdf(file_path)
        elif content_type == "excel":
            self.player.display_excel(file_path)
        elif content_type == "video":
            self.player.display_video(file_path)
        else:
            print(f"NieobsĹ‚ugiwany typ treĹ›ci: {content_type}")


if __name__ == "__main__":
    client = DigitalSignageClient()
    client.run()




