"""
Klient wyświetlacza - komunikacja z serwerem
"""
import requests
import time
import threading
from typing import Optional, Dict, Any
from datetime import datetime

import config


class DisplayClient:
    """Klient do komunikacji z serwerem"""

    def __init__(self):
        self.server_url = config.SERVER_URL
        self.mac_address = config.MAC_ADDRESS
        self.display_id: Optional[int] = None
        self.session = requests.Session()
        self.running = False
        self.heartbeat_thread: Optional[threading.Thread] = None

    def register(self) -> bool:
        """Rejestracja wyświetlacza na serwerze"""
        try:
            response = self.session.post(
                f"{self.server_url}/displays/register",
                json={
                    "mac_address": self.mac_address,
                    "ip_address": self._get_local_ip(),
                    "resolution_width": config.RESOLUTION_WIDTH,
                    "resolution_height": config.RESOLUTION_HEIGHT,
                },
            )
            if response.status_code == 201:
                data = response.json()
                self.display_id = data["id"]
                print(f"Zarejestrowano wyświetlacz: ID={self.display_id}")
                return True
            else:
                print(f"Błąd rejestracji: {response.status_code}")
                return False
        except Exception as e:
            print(f"Błąd rejestracji: {e}")
            return False

    def get_config(self) -> Optional[Dict[str, Any]]:
        """Pobranie konfiguracji wyświetlacza"""
        if not self.display_id:
            return None

        try:
            response = self.session.get(f"{self.server_url}/displays/{self.display_id}")
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Błąd pobierania konfiguracji: {e}")
        return None

    def get_schedule(self) -> list:
        """Pobranie harmonogramu dla wyświetlacza"""
        if not self.display_id:
            return []

        try:
            response = self.session.get(
                f"{self.server_url}/schedules/display/{self.display_id}/schedule"
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Błąd pobierania harmonogramu: {e}")
        return []

    def send_heartbeat(self, current_content_id: Optional[int] = None) -> bool:
        """Wysłanie heartbeat do serwera"""
        if not self.display_id:
            return False

        try:
            response = self.session.post(
                f"{self.server_url}/displays/{self.display_id}/heartbeat",
                json={
                    "current_content_id": current_content_id,
                    "cache_status": {},
                    "errors": [],
                },
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Błąd heartbeat: {e}")
            return False

    def download_content(self, content_id: int, file_path: str) -> bool:
        """Pobranie treści z serwera"""
        try:
            response = self.session.get(
                f"{self.server_url}/content/{content_id}/download",
                stream=True,
            )
            if response.status_code == 200:
                with open(file_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                return True
        except Exception as e:
            print(f"Błąd pobierania treści: {e}")
        return False

    def start_heartbeat(self):
        """Uruchomienie wątku heartbeat"""
        self.running = True
        self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self.heartbeat_thread.start()

    def stop_heartbeat(self):
        """Zatrzymanie wątku heartbeat"""
        self.running = False
        if self.heartbeat_thread:
            self.heartbeat_thread.join()

    def _heartbeat_loop(self):
        """Pętla heartbeat"""
        while self.running:
            self.send_heartbeat()
            time.sleep(config.HEARTBEAT_INTERVAL)

    def _get_local_ip(self) -> str:
        """Pobranie lokalnego adresu IP"""
        try:
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"



