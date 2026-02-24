# Konfiguracja klienta wyświetlacza
import os

# URL serwera
SERVER_URL = os.getenv("SERVER_URL", "https://dev.witold.ovh/api/v1")

# MAC address wyświetlacza (do rejestracji)
# Pobranie MAC address systemu
import uuid
MAC_ADDRESS = os.getenv(
    "MAC_ADDRESS",
    ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) for elements in range(0,2*6,2)][::-1]),
)

# Katalog cache lokalnego
CACHE_DIR = os.getenv("CACHE_DIR", "./cache")

# Interwał heartbeat (sekundy)
HEARTBEAT_INTERVAL = int(os.getenv("HEARTBEAT_INTERVAL", "30"))

# Interwał pobierania harmonogramu (sekundy)
SCHEDULE_UPDATE_INTERVAL = int(os.getenv("SCHEDULE_UPDATE_INTERVAL", "300"))

# Orientacja ekranu (0, 90, 180, 270)
ORIENTATION = int(os.getenv("ORIENTATION", "0"))

# Rozdzielczość ekranu
RESOLUTION_WIDTH = int(os.getenv("RESOLUTION_WIDTH", "1920"))
RESOLUTION_HEIGHT = int(os.getenv("RESOLUTION_HEIGHT", "1080"))



