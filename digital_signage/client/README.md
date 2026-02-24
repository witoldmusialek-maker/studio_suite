# Klient Wyświetlacza

Aplikacja klienta dla wyświetlaczy HP T630 z systemem Linux.

## Struktura

```
client/
├── main.py           # Główny plik aplikacji
├── display_client.py # Klasa klienta wyświetlacza
├── player.py         # Odtwarzanie treści
├── cache.py          # Zarządzanie cache
├── config.py         # Konfiguracja
├── requirements.txt
└── digital-signage-client.service  # Systemd service
```

## Instalacja

```bash
cd client
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Konfiguracja

Skopiuj `config.example.py` do `config.py` i uzupełnij:
- `SERVER_URL` - URL serwera
- `MAC_ADDRESS` - MAC address wyświetlacza

## Uruchomienie

```bash
python main.py
```

## Radio Bell Client (T620 / radiowezel)

Tryb audio-only, bez UI wyswietlacza:

1. Skopiuj `radio_config.example.py` do `radio_config.py` i ustaw:
- `SERVER_URL`
- `MAC_ADDRESS`
- `DISPLAY_NAME`

2. Uruchom:

```bash
python radio_client.py
```

Klient:
- rejestruje sie jako display
- pobiera komendy dzwonkow z backendu
- pobiera plik audio (`/bells/{id}/sound-file`)
- odtwarza lokalnie
- wysyla `mark-played`
- gdy nie ma dzwonka, sprawdza aktywna playliste przerwy (`/bells/display/{display_id}/music-playlist`)
- odtwarza utwory playlisty po kolei w czasie okna przerwy

## Test zewnętrzny (1 display + 1 radio client)

Dla testu przez internet ustaw w kliencie:
- `SERVER_URL = "https://dev.witold.ovh/api/v1"`

Przykład uruchomienia bez edycji `config.py` (zmienne środowiskowe):

```bash
export SERVER_URL="https://dev.witold.ovh/api/v1"
export MAC_ADDRESS="02:11:22:33:44:55"
python main.py
```

Radio client:

```bash
export SERVER_URL="https://dev.witold.ovh/api/v1"
export MAC_ADDRESS="02:AA:BB:CC:DD:EE"
python radio_client.py
```

Windows bell client (minimal):

```powershell
$env:SERVER_URL="https://dev.witold.ovh/api/v1"
$env:MAC_ADDRESS="02:AA:BB:CC:DD:EF"
python windows_bell_client.py
```

Download EXE (gotowy build):
- `digital_signage/client/download/windows_bell_client.exe`
- `digital_signage/client/download/windows_display_client.exe`

Bezpośrednio z serwera:
- `https://dev.witold.ovh/download/windows_bell_client.exe`
- `https://dev.witold.ovh/download/windows_display_client.exe`

Rozróżnienie klientów:
- `windows_bell_client.exe` = klient dzwonków (audio-only, brak wyświetlania treści).
- `windows_display_client.exe` = klient treści (obrazy/PDF/Excel/wideo na panelu).

## Systemd Service

```bash
sudo cp digital-signage-client.service /etc/systemd/system/
sudo systemctl enable digital-signage-client
sudo systemctl start digital-signage-client
```



