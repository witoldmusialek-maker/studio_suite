# Konfiguracja klienta wyświetlacza

# URL serwera
SERVER_URL = "http://192.168.200.116:8000/api/v1"

# MAC address wyświetlacza (do rejestracji)
# Pobranie MAC address systemu
import uuid
MAC_ADDRESS = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) for elements in range(0,2*6,2)][::-1])

# Katalog cache lokalnego
CACHE_DIR = "./cache"

# Interwał heartbeat (sekundy)
HEARTBEAT_INTERVAL = 30

# Interwał pobierania harmonogramu (sekundy)
SCHEDULE_UPDATE_INTERVAL = 300

# Orientacja ekranu (0, 90, 180, 270)
ORIENTATION = 0

# Rozdzielczość ekranu
RESOLUTION_WIDTH = 1920
RESOLUTION_HEIGHT = 1080



