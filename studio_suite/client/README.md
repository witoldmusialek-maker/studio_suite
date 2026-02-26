# Klient WyĹ›wietlacza

Aplikacja klienta dla wyĹ›wietlaczy HP T630 z systemem Linux.

## Struktura

```
client/
â”śâ”€â”€ main.py           # GĹ‚Ăłwny plik aplikacji
â”śâ”€â”€ display_client.py # Klasa klienta wyĹ›wietlacza
â”śâ”€â”€ player.py         # Odtwarzanie treĹ›ci
â”śâ”€â”€ cache.py          # ZarzÄ…dzanie cache
â”śâ”€â”€ config.py         # Konfiguracja
â”śâ”€â”€ requirements.txt
â””â”€â”€ digital-signage-client.service  # Systemd service
```

## Instalacja

```bash
cd client
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Konfiguracja

Skopiuj `config.example.py` do `config.py` i uzupeĹ‚nij:
- `SERVER_URL` - URL serwera
- `MAC_ADDRESS` - MAC address wyĹ›wietlacza

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

## Test zewnÄ™trzny (1 display + 1 radio client)

Dla testu przez internet ustaw w kliencie:
- `SERVER_URL = "https://dev2.witold.ovh/api/v1"`

PrzykĹ‚ad uruchomienia bez edycji `config.py` (zmienne Ĺ›rodowiskowe):

```bash
export SERVER_URL="https://dev2.witold.ovh/api/v1"
export MAC_ADDRESS="02:11:22:33:44:55"
python main.py
```

Radio client:

```bash
export SERVER_URL="https://dev2.witold.ovh/api/v1"
export MAC_ADDRESS="02:AA:BB:CC:DD:EE"
python radio_client.py
```

Windows bell client (minimal):

```powershell
$env:SERVER_URL="https://dev2.witold.ovh/api/v1"
$env:MAC_ADDRESS="02:AA:BB:CC:DD:EF"
python windows_bell_client.py
```

Download EXE (gotowy build):
- `studio_suite/client/download/windows_bell_client.exe`
- `studio_suite/client/download/windows_display_client.exe`

BezpoĹ›rednio z serwera:
- `https://dev2.witold.ovh/download/windows_bell_client.exe`
- `https://dev2.witold.ovh/download/windows_display_client.exe`

RozrĂłĹĽnienie klientĂłw:
- `windows_bell_client.exe` = klient dzwonkĂłw (audio-only, brak wyĹ›wietlania treĹ›ci).
- `windows_display_client.exe` = klient treĹ›ci (obrazy/PDF/Excel/wideo na panelu).

## Systemd Service

```bash
sudo cp digital-signage-client.service /etc/systemd/system/
sudo systemctl enable digital-signage-client
sudo systemctl start digital-signage-client
```




