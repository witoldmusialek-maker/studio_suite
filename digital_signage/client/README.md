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

## Systemd Service

```bash
sudo cp digital-signage-client.service /etc/systemd/system/
sudo systemctl enable digital-signage-client
sudo systemctl start digital-signage-client
```



