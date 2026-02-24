# Konfiguracja radio-client (T620 / radiowezel)

# URL API (z /api/v1)
# Lokalnie: "http://localhost:8000/api/v1"
# Zdalnie: "https://dev.witold.ovh/api/v1"
SERVER_URL = "http://localhost:8000/api/v1"

# Identyfikator urządzenia audio (rejestrowany jako display)
MAC_ADDRESS = "02:AA:BB:CC:DD:EE"
DISPLAY_NAME = "radio-node-t620"

# Parametry rejestracji display
RESOLUTION_WIDTH = 1
RESOLUTION_HEIGHT = 1

# Interwały (sekundy)
POLL_INTERVAL = 2
HEARTBEAT_INTERVAL = 30

# Lokalny cache plików audio
CACHE_DIR = "./radio_cache"
