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

## Systemd Service

```bash
sudo cp digital-signage-client.service /etc/systemd/system/
sudo systemctl enable digital-signage-client
sudo systemctl start digital-signage-client
```



