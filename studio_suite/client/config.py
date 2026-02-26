# Konfiguracja klienta wyœwietlacza
import os
import uuid

# URL serwera
SERVER_URL = os.getenv("SERVER_URL", "https://dev2.witold.ovh/api/v1")

# MAC address wyœwietlacza (do rejestracji)
MAC_ADDRESS = os.getenv(
    "MAC_ADDRESS",
    ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) for elements in range(0, 2 * 6, 2)][::-1]),
)

# Katalog cache lokalnego
CACHE_DIR = os.getenv("CACHE_DIR", "./cache")

# Interwa³ heartbeat (sekundy)
HEARTBEAT_INTERVAL = int(os.getenv("HEARTBEAT_INTERVAL", "30"))

# Interwa³ pêtli odpytywania treœci (sekundy)
POLL_INTERVAL_SECONDS = int(os.getenv("POLL_INTERVAL_SECONDS", "10"))

# Plik logu debug klienta
DEBUG_LOG_FILE = os.getenv("DEBUG_LOG_FILE", "./windows_display_client.log")

# Ustawienie okna na wierzchu (kiosk). Zalecane 0 podczas testów.
WINDOW_TOPMOST = os.getenv("WINDOW_TOPMOST", "0") == "1"

# Ukrycie kursora myszy
HIDE_CURSOR = os.getenv("HIDE_CURSOR", "1") == "1"

# Orientacja ekranu (0, 90, 180, 270)
ORIENTATION = int(os.getenv("ORIENTATION", "0"))

# Rozdzielczoœæ ekranu
RESOLUTION_WIDTH = int(os.getenv("RESOLUTION_WIDTH", "1920"))
RESOLUTION_HEIGHT = int(os.getenv("RESOLUTION_HEIGHT", "1080"))
